package internal

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net"
	"net/url"
	"strings"
	"time"

	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
	"github.com/openai/openai-go/shared"
)

const systemPrompt = `Ты извлекаешь сведения из сообщения бюро находок.
Верни один JSON-объект и ничего больше: без markdown и без пояснений.
Ключи ровно эти, все обязательны: category, summary, location_code, item_description, event_time, details.
category - одно из: lost (потеря вещи), found (находка), claim (сообщение, что найденная вещь принадлежит автору), other (остальное или неоднозначная тема).
summary - краткое содержание, непустая строка.
location_code - код локации из текста, например LOC-03, или null. Если есть только название места без кода, ставь null.
item_description - описание вещи или null.
event_time - время потери, находки или другого события текстом как в сообщении, или null. Даты и время не пересчитывай.
details - существенные сведения, которые не вошли в остальные поля, или null.
Не выдумывай отсутствующие сведения. Для пустого поля пиши JSON null без кавычек, не пустую строку и не текст null. Числа и списки не используй: только строка или null.`

var categories = map[string]struct{}{
	"lost":  {},
	"found": {},
	"claim": {},
	"other": {},
}

var requiredKeys = []string{
	"category", "summary", "location_code", "item_description", "event_time", "details",
}

type Extraction struct {
	Category        string
	Summary         string
	LocationCode    *string
	ItemDescription *string
	EventTime       *string
	Details         *string
}

type extractionJSON struct {
	Category        string  `json:"category"`
	Summary         string  `json:"summary"`
	LocationCode    *string `json:"location_code"`
	ItemDescription *string `json:"item_description"`
	EventTime       *string `json:"event_time"`
	Details         *string `json:"details"`
}

type StatusError struct {
	Status  int
	Code    string
	Message string
}

func (e *StatusError) Error() string { return e.Message }

type LLM struct {
	Client  openai.Client
	Model   string
	Temp    float64
	Timeout time.Duration
}

func NewLLM(apiKey, baseURL, model string, temp float64, timeout time.Duration) *LLM {
	client := openai.NewClient(
		option.WithAPIKey(apiKey),
		option.WithBaseURL(OpenAIBase(baseURL)),
	)
	return &LLM{Client: client, Model: model, Temp: temp, Timeout: timeout}
}

func OpenAIBase(raw string) string {
	raw = strings.TrimRight(strings.TrimSpace(raw), "/")
	if strings.HasSuffix(raw, "/api/v1") {
		return strings.TrimSuffix(raw, "/api/v1") + "/v1"
	}
	return raw
}

var extractionSchema = map[string]any{
	"type":                 "object",
	"additionalProperties": false,
	"required":             []string{"category", "summary", "location_code", "item_description", "event_time", "details"},
	"properties": map[string]any{
		"category":         map[string]any{"type": "string", "enum": []string{"lost", "found", "claim", "other"}},
		"summary":          map[string]any{"type": "string"},
		"location_code":    map[string]any{"type": []string{"string", "null"}},
		"item_description": map[string]any{"type": []string{"string", "null"}},
		"event_time":       map[string]any{"type": []string{"string", "null"}},
		"details":          map[string]any{"type": []string{"string", "null"}},
	},
}

func (l *LLM) Extract(ctx context.Context, message string) (Extraction, error) {
	ctx, cancel := context.WithTimeout(ctx, l.Timeout)
	defer cancel()

	// Chat Completions: LM Studio здесь принимает response_format и отдаёт content чистым JSON.
	resp, err := l.Client.Chat.Completions.New(ctx, openai.ChatCompletionNewParams{
		Model:           shared.ChatModel(l.Model),
		Temperature:     openai.Float(l.Temp),
		ReasoningEffort: shared.ReasoningEffort("none"),
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.SystemMessage(systemPrompt),
			openai.UserMessage(message),
		},
		ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
			OfJSONSchema: &shared.ResponseFormatJSONSchemaParam{
				JSONSchema: shared.ResponseFormatJSONSchemaJSONSchemaParam{
					Name:   "lost_found",
					Strict: openai.Bool(true),
					Schema: extractionSchema,
				},
			},
		},
	})
	if err != nil {
		return Extraction{}, modelCallError(err)
	}
	if len(resp.Choices) == 0 {
		return Extraction{}, &StatusError{
			Status:  502,
			Code:    "invalid_model_response",
			Message: "Ответ модели не является допустимым JSON по схеме",
		}
	}

	text := strings.TrimSpace(resp.Choices[0].Message.Content)
	ex, err := ParseExtraction(text)
	if err != nil {
		log.Printf("ответ модели не прошёл схему: %v; текст: %s", err, clip(text, 500))
		return Extraction{}, &StatusError{
			Status:  502,
			Code:    "invalid_model_response",
			Message: "Ответ модели не является допустимым JSON по схеме",
		}
	}
	return ex, nil
}

func modelCallError(err error) error {
	if errors.Is(err, context.DeadlineExceeded) {
		return &StatusError{Status: 504, Code: "model_timeout", Message: "Превышено время ожидания модели"}
	}
	var netErr net.Error
	if errors.As(err, &netErr) && netErr.Timeout() {
		return &StatusError{Status: 504, Code: "model_timeout", Message: "Превышено время ожидания модели"}
	}
	var urlErr *url.Error
	if errors.As(err, &urlErr) && urlErr.Timeout() {
		return &StatusError{Status: 504, Code: "model_timeout", Message: "Превышено время ожидания модели"}
	}
	var apiErr *openai.Error
	if errors.As(err, &apiErr) && (apiErr.StatusCode == 408 || apiErr.StatusCode == 504) {
		return &StatusError{Status: 504, Code: "model_timeout", Message: "Превышено время ожидания модели"}
	}
	log.Printf("сервер модели недоступен: %v", err)
	return &StatusError{Status: 503, Code: "model_unavailable", Message: "Сервер модели недоступен"}
}

func ParseExtraction(raw string) (Extraction, error) {
	return decodeExtraction(strings.TrimSpace(strings.TrimPrefix(raw, "\uFEFF")))
}

func decodeExtraction(raw string) (Extraction, error) {
	var obj map[string]json.RawMessage
	if err := json.Unmarshal([]byte(raw), &obj); err != nil || obj == nil {
		return Extraction{}, fmt.Errorf("ожидался JSON-объект")
	}
	if len(obj) != len(requiredKeys) {
		return Extraction{}, fmt.Errorf("число полей должно быть %d", len(requiredKeys))
	}
	for _, key := range requiredKeys {
		if _, ok := obj[key]; !ok {
			return Extraction{}, fmt.Errorf("нет поля %s", key)
		}
	}

	dec := json.NewDecoder(strings.NewReader(raw))
	dec.DisallowUnknownFields()
	var body extractionJSON
	if err := dec.Decode(&body); err != nil {
		return Extraction{}, err
	}
	if dec.More() {
		return Extraction{}, fmt.Errorf("после JSON есть лишние данные")
	}

	body.Category = strings.TrimSpace(body.Category)
	body.Summary = strings.TrimSpace(body.Summary)
	if body.Category == "" || body.Summary == "" {
		return Extraction{}, fmt.Errorf("category и summary должны быть непустыми")
	}
	if _, ok := categories[body.Category]; !ok {
		return Extraction{}, fmt.Errorf("недопустимая категория")
	}

	return Extraction{
		Category:        body.Category,
		Summary:         body.Summary,
		LocationCode:    clean(body.LocationCode),
		ItemDescription: clean(body.ItemDescription),
		EventTime:       clean(body.EventTime),
		Details:         clean(body.Details),
	}, nil
}

func clean(value *string) *string {
	if value == nil {
		return nil
	}
	trimmed := strings.TrimSpace(*value)
	if trimmed == "" || strings.EqualFold(trimmed, "null") {
		return nil
	}
	return &trimmed
}

func clip(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

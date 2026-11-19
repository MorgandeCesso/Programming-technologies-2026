package internal

import (
	"errors"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type Handler struct {
	DB  *gorm.DB
	LLM *LLM
}

type CreateRequest struct {
	Message string `json:"message" binding:"required" example:"Сегодня около 10 утра нашёл чёрный зонт у стойки охраны, локация LOC-03. На ручке красная лента."`
}

type RecordResponse struct {
	ID              uint      `json:"id"`
	CreatedAt       time.Time `json:"created_at"`
	Message         string    `json:"message"`
	Category        string    `json:"category" enums:"lost,found,claim,other"`
	Summary         string    `json:"summary"`
	LocationCode    *string   `json:"location_code"`
	ItemDescription *string   `json:"item_description"`
	EventTime       *string   `json:"event_time"`
	Details         *string   `json:"details"`
	LocationID      *uint     `json:"location_id"`
	MatchStatus     string    `json:"match_status" enums:"matched,not_found,not_provided"`
}

type ErrorResponse struct {
	Error   string `json:"error" example:"bad_request"`
	Message string `json:"message" example:"Поле message обязательно и не может состоять из пробелов"`
}

func NewHandler(db *gorm.DB, llm *LLM) *Handler {
	return &Handler{DB: db, LLM: llm}
}

// Create принимает текст, вызывает модель, проверяет ответ и сохраняет запись.
//
//	@Summary		Принять сообщение
//	@Tags			lost-found
//	@Accept			json
//	@Produce		json
//	@Param			body	body		CreateRequest	true	"Текст сообщения"
//	@Success		201		{object}	RecordResponse
//	@Failure		400		{object}	ErrorResponse
//	@Failure		502		{object}	ErrorResponse
//	@Failure		503		{object}	ErrorResponse
//	@Failure		504		{object}	ErrorResponse
//	@Router			/lost-found [post]
func (h *Handler) Create(c *gin.Context) {
	var req CreateRequest
	if err := c.ShouldBindJSON(&req); err != nil || strings.TrimSpace(req.Message) == "" {
		writeError(c, http.StatusBadRequest, "bad_request", "Поле message обязательно и не может состоять из пробелов")
		return
	}

	ex, err := h.LLM.Extract(c.Request.Context(), strings.TrimSpace(req.Message))
	if err != nil {
		writeStatus(c, err)
		return
	}

	row, err := SaveMessage(h.DB, strings.TrimSpace(req.Message), ex)
	if err != nil {
		writeError(c, http.StatusInternalServerError, "internal_error", "Не удалось сохранить запись")
		return
	}
	c.JSON(http.StatusCreated, toResponse(row))
}

// List возвращает сохранённые записи без повторного вызова модели.
//
//	@Summary	Список сообщений
//	@Tags		lost-found
//	@Produce	json
//	@Success	200	{array}	RecordResponse
//	@Router		/lost-found [get]
func (h *Handler) List(c *gin.Context) {
	rows, err := ListMessages(h.DB)
	if err != nil {
		writeError(c, http.StatusInternalServerError, "internal_error", "Не удалось прочитать записи")
		return
	}
	out := make([]RecordResponse, 0, len(rows))
	for _, row := range rows {
		out = append(out, toResponse(row))
	}
	c.JSON(http.StatusOK, out)
}

// Get возвращает одну запись.
//
//	@Summary		Одна запись
//	@Tags			lost-found
//	@Produce		json
//	@Param			id	path		int	true	"ID записи"
//	@Success		200	{object}	RecordResponse
//	@Failure		400	{object}	ErrorResponse
//	@Failure		404	{object}	ErrorResponse
//	@Router			/lost-found/{id} [get]
func (h *Handler) Get(c *gin.Context) {
	id64, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil || id64 == 0 {
		writeError(c, http.StatusBadRequest, "bad_request", "Некорректный id")
		return
	}
	row, err := GetMessage(h.DB, uint(id64))
	if errors.Is(err, gorm.ErrRecordNotFound) {
		writeError(c, http.StatusNotFound, "not_found", "Запись не найдена")
		return
	}
	if err != nil {
		writeError(c, http.StatusInternalServerError, "internal_error", "Не удалось прочитать запись")
		return
	}
	c.JSON(http.StatusOK, toResponse(row))
}

func toResponse(row Message) RecordResponse {
	return RecordResponse{
		ID:              row.ID,
		CreatedAt:       row.CreatedAt,
		Message:         row.SourceText,
		Category:        row.Category,
		Summary:         row.Summary,
		LocationCode:    row.LocationCode,
		ItemDescription: row.ItemDescription,
		EventTime:       row.EventTime,
		Details:         row.Details,
		LocationID:      row.LocationID,
		MatchStatus:     row.MatchStatus,
	}
}

func writeStatus(c *gin.Context, err error) {
	var status *StatusError
	if errors.As(err, &status) {
		writeError(c, status.Status, status.Code, status.Message)
		return
	}
	writeError(c, http.StatusInternalServerError, "internal_error", "Внутренняя ошибка")
}

func writeError(c *gin.Context, status int, code, message string) {
	c.JSON(status, ErrorResponse{Error: code, Message: message})
}

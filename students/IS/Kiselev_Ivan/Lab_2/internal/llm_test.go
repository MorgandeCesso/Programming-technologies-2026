package internal

import "testing"

func TestParseLabExample(t *testing.T) {
	raw := `{
	  "category": "found",
	  "summary": "Найден чёрный зонт у стойки охраны.",
	  "location_code": "LOC-03",
	  "item_description": "Чёрный зонт с красной лентой на ручке",
	  "event_time": "сегодня около 10 утра",
	  "details": null
	}`
	ex, err := ParseExtraction(raw)
	if err != nil {
		t.Fatal(err)
	}
	if ex.Category != "found" || ex.LocationCode == nil || *ex.LocationCode != "LOC-03" || ex.Details != nil {
		t.Fatalf("%+v", ex)
	}
}

func TestParseEmptyNullableBecomesNull(t *testing.T) {
	raw := `{
	  "category": "lost",
	  "summary": "Потеряны перчатки.",
	  "location_code": "  ",
	  "item_description": "Перчатки",
	  "event_time": "",
	  "details": null
	}`
	ex, err := ParseExtraction(raw)
	if err != nil {
		t.Fatal(err)
	}
	if ex.LocationCode != nil || ex.EventTime != nil {
		t.Fatalf("пустые строки должны стать null: %+v", ex)
	}
}

func TestParseRejects(t *testing.T) {
	cases := []string{
		`{"category":"other","summary":"Вопрос.","location_code":null,"item_description":null,"event_time":null}`,
		`{"category":"other","summary":"Вопрос.","location_code":null,"item_description":null,"event_time":null,"details":null,"extra":1}`,
		`{"category":"unknown","summary":"Вопрос.","location_code":null,"item_description":null,"event_time":null,"details":null}`,
		`{"category":"other","summary":"   ","location_code":null,"item_description":null,"event_time":null,"details":null}`,
		`{"category":"other","summary":"Вопрос.","location_code":12,"item_description":null,"event_time":null,"details":null}`,
		`{"category":"other","summary":"Вопрос.","location_code":null,"item_description":["зонт"],"event_time":null,"details":null}`,
	}
	for _, raw := range cases {
		if _, err := ParseExtraction(raw); err == nil {
			t.Fatalf("ожидалась ошибка: %s", raw)
		}
	}
}

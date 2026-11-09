package internal

import (
	"errors"
	"strings"
	"time"

	"gorm.io/gorm"
)

type Location struct {
	ID   uint   `gorm:"primaryKey"`
	Code string `gorm:"uniqueIndex;size:64;not null"`
	Name string `gorm:"size:255;not null"`
}

type Message struct {
	ID              uint `gorm:"primaryKey"`
	CreatedAt       time.Time
	SourceText      string `gorm:"not null"`
	Category        string `gorm:"not null"`
	Summary         string `gorm:"not null"`
	LocationCode    *string
	ItemDescription *string
	EventTime       *string
	Details         *string
	LocationID      *uint
	MatchStatus     string `gorm:"not null"`
}

func MigrateAndSeed(db *gorm.DB) error {
	if err := db.AutoMigrate(&Location{}, &Message{}); err != nil {
		return err
	}
	seed := []Location{
		{Code: "LOC-01", Name: "Вестибюль"},
		{Code: "LOC-02", Name: "Гардероб"},
		{Code: "LOC-03", Name: "Стойка охраны"},
		{Code: "LOC-04", Name: "Читальный зал"},
		{Code: "LOC-05", Name: "Столовая"},
	}
	for _, loc := range seed {
		row := loc
		if err := db.Where("code = ?", row.Code).FirstOrCreate(&row).Error; err != nil {
			return err
		}
	}
	return nil
}

func FindLocation(db *gorm.DB, code string) (*Location, error) {
	var loc Location
	err := db.Where("LOWER(BTRIM(code)) = LOWER(?)", strings.TrimSpace(code)).First(&loc).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &loc, nil
}

func SaveMessage(db *gorm.DB, source string, ex Extraction) (Message, error) {
	msg := Message{
		SourceText:      source,
		Category:        ex.Category,
		Summary:         ex.Summary,
		LocationCode:    ex.LocationCode,
		ItemDescription: ex.ItemDescription,
		EventTime:       ex.EventTime,
		Details:         ex.Details,
		MatchStatus:     "not_provided",
	}
	if ex.LocationCode != nil {
		loc, err := FindLocation(db, *ex.LocationCode)
		if err != nil {
			return Message{}, err
		}
		if loc == nil {
			msg.MatchStatus = "not_found"
		} else {
			msg.MatchStatus = "matched"
			msg.LocationID = &loc.ID
		}
	}
	if err := db.Create(&msg).Error; err != nil {
		return Message{}, err
	}
	return msg, nil
}

func ListMessages(db *gorm.DB) ([]Message, error) {
	var rows []Message
	err := db.Order("id desc").Find(&rows).Error
	return rows, err
}

func GetMessage(db *gorm.DB, id uint) (Message, error) {
	var row Message
	err := db.First(&row, id).Error
	return row, err
}

package main

import (
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"Lab_2/docs"
	"Lab_2/internal"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

//	@title			Бюро находок
//	@version		1.0
//	@description	Сообщения о находках и потерях: извлечение полей локальной моделью и сохранение в PostgreSQL
//	@host			localhost:8080
//	@BasePath		/

func main() {
	_ = godotenv.Load()

	apiKey := os.Getenv("API_KEY")
	baseURL := os.Getenv("BASE_URL")
	model := os.Getenv("MODEL_2") // Приоритетно берётся подходящий nemotron
	if model == "" {
		model = os.Getenv("MODEL_1")
	}
	dsn := os.Getenv("DATABASE_URL")
	if apiKey == "" || baseURL == "" || model == "" || dsn == "" {
		log.Fatal("в .env нужны API_KEY, BASE_URL, MODEL_2 или MODEL_1 и DATABASE_URL")
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	temp := 0.2
	if raw := os.Getenv("TEMPERATURE"); raw != "" {
		if parsed, err := strconv.ParseFloat(raw, 64); err == nil {
			temp = parsed
		}
	}
	timeout := 120 * time.Second
	if raw := os.Getenv("LLM_TIMEOUT_SEC"); raw != "" {
		if parsed, err := strconv.Atoi(raw); err == nil && parsed > 0 {
			timeout = time.Duration(parsed) * time.Second
		}
	}

	db := openDB(dsn)
	if err := internal.MigrateAndSeed(db); err != nil {
		log.Fatal(err)
	}

	llm := internal.NewLLM(apiKey, baseURL, model, temp, timeout)
	h := internal.NewHandler(db, llm)

	docs.SwaggerInfo.Host = "localhost:" + port
	r := gin.Default()
	r.POST("/lost-found", h.Create)
	r.GET("/lost-found", h.List)
	r.GET("/lost-found/:id", h.Get)
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	log.Printf("модель %s, openai %s", model, internal.OpenAIBase(baseURL))
	srv := &http.Server{
		Addr:              ":" + port,
		Handler:           r,
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      timeout + 10*time.Second,
	}
	log.Fatal(srv.ListenAndServe())
}

func openDB(dsn string) *gorm.DB {
	var db *gorm.DB
	var err error
	for i := 1; i <= 15; i++ {
		db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
		if err == nil {
			sqlDB, dbErr := db.DB()
			if dbErr == nil {
				err = sqlDB.Ping()
			} else {
				err = dbErr
			}
		}
		if err == nil {
			return db
		}
		log.Printf("postgres ещё не готов (%d/15): %v", i, err)
		time.Sleep(time.Second)
	}
	log.Fatal(err)
	return nil
}

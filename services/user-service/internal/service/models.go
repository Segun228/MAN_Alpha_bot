package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

var retryDelays = []time.Duration{
	5 * time.Second,
	10 * time.Second,
}

func doWithRetry(req *http.Request, out any) (*http.Response, error) {
	var lastErr error

	for attempt := 0; attempt <= len(retryDelays); attempt++ {
		client := &http.Client{Timeout: 20 * time.Second}

		resp, err := client.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("network error: %w", err)
		} else {
			bodyCopy := bytes.Buffer{}
			_, copyErr := io.Copy(&bodyCopy, resp.Body)
			resp.Body.Close()

			if copyErr != nil {
				lastErr = fmt.Errorf("read error: %w", copyErr)
			} else if bodyCopy.Len() == 0 {
				lastErr = fmt.Errorf("empty body")
			} else {
				if jsonErr := json.Unmarshal(bodyCopy.Bytes(), out); jsonErr != nil {
					lastErr = fmt.Errorf("invalid json: %w", jsonErr)
				} else {
					resp.Body = io.NopCloser(bytes.NewBuffer(bodyCopy.Bytes()))
					return resp, nil
				}
			}
		}

		if attempt < len(retryDelays) {
			time.Sleep(retryDelays[attempt])
		}
	}

	return nil, fmt.Errorf("request failed after retries: %w", lastErr)
}

type ModelService struct {
	ChatModelUrl string
	DocsModelUrl string
	SummModel    string
	RecsModelUrl string
	AnalizerUrl  string
}

func NewModelService(
	chatModelUrl string,
	docsModelUrl string,
	summModel string,
	recsModelUrl string,
	analizerUrl string,
) *ModelService {
	return &ModelService{
		ChatModelUrl: chatModelUrl,
		DocsModelUrl: docsModelUrl,
		SummModel:    summModel,
		RecsModelUrl: recsModelUrl,
		AnalizerUrl:  analizerUrl,
	}
}

type AskChatModelRequest struct {
	Text     string           `json:"text"`
	Business string           `json:"business"`
	Context  ChatModelContext `json:"context"`
}

type ChatModelContext struct {
	History []Message `json:"history"`
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ResponseData struct {
	Success  bool           `json:"success"`
	Response string         `json:"response"`
	Usage    map[string]any `json:"usage"`
	Model    string         `json:"model"`
}

func (s *ModelService) AskChatModel(ctx context.Context, input AskChatModelRequest) (string, error) {
	if s.ChatModelUrl == "" {
		return "", fmt.Errorf("model service is not configured")
	}

	data, err := json.Marshal(input)
	if err != nil {
		return "", fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.ChatModelUrl+"/generate_response", bytes.NewBuffer(data))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	var resData ResponseData
	resp, err := doWithRetry(req, &resData)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	return resData.Response, nil
}

func (s *ModelService) AskDocsMode(ctx context.Context, text string) (string, error) {
	if s.DocsModelUrl == "" {
		return "", fmt.Errorf("docs model service is not configured")
	}

	payload := map[string]string{"question": text}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.DocsModelUrl+"/generate_response", bytes.NewBuffer(data))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	var raw map[string]any
	resp, err := doWithRetry(req, &raw)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if arr, ok := raw["response"].([]any); ok {
		out := ""
		for i, v := range arr {
			if s, ok := v.(string); ok {
				if i > 0 {
					out += "\n"
				}
				out += s
			}
		}
		return out, nil
	}

	if s, ok := raw["response"].(string); ok {
		return s, nil
	}

	b, _ := json.Marshal(raw)
	return string(b), nil
}

type SummarizerResponse struct {
	Success  bool           `json:"success"`
	Response string         `json:"response"`
	Usage    map[string]any `json:"usage"`
	Model    string         `json:"model"`
}

func (s *ModelService) AskSummarizerFirst(ctx context.Context, text string) (string, error) {
	if s.SummModel == "" {
		return "", fmt.Errorf("summarizer first model service is not configured")
	}

	payload := map[string]string{"text": text}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.SummModel+"/summarize/text", bytes.NewBuffer(data))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	var out SummarizerResponse
	resp, err := doWithRetry(req, &out)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	return out.Response, nil
}

type SummarizerSecondRequest struct {
	Text    string    `json:"text"`
	Context []Message `json:"context"`
}

func (s *ModelService) AskSummarizerSecond(ctx context.Context, input SummarizerSecondRequest) (string, error) {
	if s.SummModel == "" {
		return "", fmt.Errorf("summarizer second model service is not configured")
	}

	data, err := json.Marshal(input)
	if err != nil {
		return "", fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.SummModel+"/summarize/dialog", bytes.NewBuffer(data))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	var out SummarizerResponse
	resp, err := doWithRetry(req, &out)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	return out.Response, nil
}

type UniversalRequest struct {
	Business    string    `json:"business"`
	Description string    `json:"description"`
	Context     []Message `json:"context"`
}

func (s *ModelService) AskRecsModel(ctx context.Context, input UniversalRequest) (string, error) {
	if s.RecsModelUrl == "" {
		return "", fmt.Errorf("recommendations model service is not configured")
	}

	data, err := json.Marshal(input)
	if err != nil {
		return "", fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.RecsModelUrl+"/recomedations", bytes.NewBuffer(data))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	var resData ResponseData
	resp, err := doWithRetry(req, &resData)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	return resData.Response, nil
}

func (s *ModelService) AskAnalyzer(ctx context.Context, input UniversalRequest, analysisType string) (string, error) {
	if s.AnalizerUrl == "" {
		return "", fmt.Errorf("analyzer model service is not configured")
	}

	url := fmt.Sprintf("%s/%s", s.AnalizerUrl, analysisType)

	body, err := json.Marshal(input)
	if err != nil {
		return "", fmt.Errorf("failed to marshal input: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	var resData ResponseData
	resp, err := doWithRetry(req, &resData)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	return resData.Response, nil
}

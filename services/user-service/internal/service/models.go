package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

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

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("model service returned non-200 status: %d", resp.StatusCode)
	}

	var resData ResponseData
	if err := json.NewDecoder(resp.Body).Decode(&resData); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	if !resData.Success {
		return "", fmt.Errorf("model service returned unsuccessful response")
	}

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

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("docs model service returned non-200 status: %d", resp.StatusCode)
	}

	var raw map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

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

	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("summarizer first model service returned non-200 status: %d", resp.StatusCode)
	}

	var out SummarizerResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	if !out.Success {
		return "", fmt.Errorf("summarizer first model service returned unsuccessful response")
	}

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

	client := &http.Client{Timeout: 20 * time.Second}

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("summarizer second model service returned non-200 status: %d", resp.StatusCode)
	}

	var out SummarizerResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	if !out.Success {
		return "", fmt.Errorf("summarizer second model service returned unsuccessful response")
	}

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

	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("recommendations model service returned non-200 status: %d", resp.StatusCode)
	}

	var resData ResponseData
	if err := json.NewDecoder(resp.Body).Decode(&resData); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	if !resData.Success {
		return "", fmt.Errorf("recommendations model service returned unsuccessful response")
	}

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

	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("analyzer model service returned non-200 status: %d", resp.StatusCode)
	}

	var resData ResponseData
	if err := json.NewDecoder(resp.Body).Decode(&resData); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	if !resData.Success {
		return "", fmt.Errorf("analyzer model service returned unsuccessful response")
	}

	return resData.Response, nil
}

package v1

import (
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"

	"github.com/Segun228/MAN_Alpha_bot/services/api-gateway/pkg/utils"
	"github.com/sirupsen/logrus"
)

type Proxy struct {
	target *url.URL
	logger utils.Logger
}

func NewProxy(targetURL string, logger utils.Logger) (*Proxy, error) {
	u, err := url.Parse(targetURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse target url: %w", err)
	}

	return &Proxy{
		target: u,
		logger: logger,
	}, nil
}

func (p *Proxy) Handler(prefix string) http.Handler {
	proxy := httputil.NewSingleHostReverseProxy(p.target)

	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		p.logger.Error("reverse proxy error", logrus.Fields{
			"error": err.Error(),
		})
		http.Error(w, "upstream service unavalable", http.StatusBadGateway)
	}

	return http.StripPrefix(prefix, proxy)
}

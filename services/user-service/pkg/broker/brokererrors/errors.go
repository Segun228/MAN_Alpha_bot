package brokererrors

import (
	"fmt"
	"strings"
)

type SerialisationError struct {
	SuccessfullCount int
	FailedCount      int
	Errors           []error
}

func (e SerialisationError) Error() string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf(
		"serialization completed with %d successes and %d failures. Failures:",
		e.SuccessfullCount, e.FailedCount,
	))

	for _, err := range e.Errors {
		sb.WriteString(fmt.Sprintf("\n- %v", err))
	}

	return sb.String()
}

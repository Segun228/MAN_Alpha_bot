package repoerrors

import "errors"

var (
	ErrNotFound      = errors.New("not found")
	ErrOwnerNotFound = errors.New("owner not found")
)

/*
These are partial implementations of either pydantic models or ersponse
models to facilitate testing
*/

package precis_test

type Feed struct {
	Id   string `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
}

type FeedEntry struct {
	Id    string `json:"id,omitempty"`
	Title string `json:"title,omitempty"`
}

type Handler struct {
	Name       string `json:"name,omitempty"`
	Type       string `json:"type,omitempty"`
	Configured bool   `json:"configured,omitempty"`
}

type Settings struct {
	SendNotification           bool   `json:"send_notification,omitempty"`
	Theme                      string `json:"theme,omitempty"`
	RefreshInterval            int    `json:"refresh_interval,omitempty"`
	ReadingSpeed               int    `json:"reading_speed,omitempty"`
	NotificationHandlerKey     string `json:"notification_handler_key,omitempty"`
	SummarizationHandlerKey    string `json:"summarization_handler_key,omitempty"`
	ContentRetrievalHandlerKey string `json:"content_retrieval_handler_key,omitempty"`
	RecentHours                int    `json:"recent_hours,omitempty"`
	FinishedOnboarding         bool   `json:"finished_onboarding,omitempty"`
}

type AboutResponse struct {
	Settings        Settings `json:"settings"`
	UpdateStatus    bool     `json:"update_status,omitempty"`
	UpdateException string   `json:"update_exception,omitempty"`
	Version         string   `json:"version,omitempty"`
	PythonVersion   string   `json:"python_version,omitempty"`
	FastAPIVersion  string   `json:"fastapi_version,omitempty"`
	Docker          bool     `json:"docker,omitempty"`
	StorageHandler  string   `json:"storage_handler,omitempty"`
	Github          string   `json:"github,omitempty"`
}

type SettingsResponse struct {
	Themes                      []string `json:"themes,omitempty"`
	ContentHandlerChoices       []string `json:"content_handler_choices,omitempty"`
	SummarizationHandlerChoices []string `json:"summarization_handler_choices,omitempty"`
	NotificationHandlerChoices  []string `json:"notification_handler_choices,omitempty"`
	UpdateStatus                bool     `json:"update_status,omitempty"`
	UpdateException             string   `json:"update_exception,omitempty"`

	Settings Settings `json:"settings,omitempty"`
}

/*
These tests test the content of the API responses
*/
package precis_test

import (
	"encoding/json"
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"
)

var client = &http.Client{}

func TestAbout(t *testing.T) {
	req, err := http.NewRequest("GET", baseURL+"/about", nil)
	req.Header.Set("accept", "application/json")

	if err != nil {
		t.Fatal(err)
	}

	res, err := client.Do(req)
	if err != nil {
		t.Fatal(err)
	}

	if res.StatusCode != http.StatusOK {
		t.Errorf("About page returned status code %d, expected %d", res.StatusCode, http.StatusOK)
	}

	var about AboutResponse

	if err := json.NewDecoder(res.Body).Decode(&about); err != nil {
		t.Fatal(err)
	}

	defer res.Body.Close()

	assert.Equal(t, false, about.UpdateStatus)
	assert.Empty(t, about.UpdateException)

	assert.NotEmpty(t, about.Version)
	assert.NotEmpty(t, about.PythonVersion)
	assert.NotEmpty(t, about.FastAPIVersion)
	assert.IsType(t, true, about.Docker)
	assert.NotEmpty(t, about, about.StorageHandler)
	assert.NotEmpty(t, about.Github)

}

func TestSettings(t *testing.T) {
	req, err := http.NewRequest("GET", baseURL+"/settings", nil)
	req.Header.Set("accept", "application/json")

	if err != nil {
		t.Fatal(err)
	}

	res, err := client.Do(req)
	if err != nil {
		t.Fatal(err)
	}

	if res.StatusCode != http.StatusOK {
		t.Errorf("Settings page returned status code %d, expected %d", res.StatusCode, http.StatusOK)
	}

	var settings SettingsResponse

	if err := json.NewDecoder(res.Body).Decode(&settings); err != nil {
		t.Fatal(err)
	}

	defer res.Body.Close()

	assert.NotEmpty(t, settings.Themes)
	assert.NotEmpty(t, settings.ContentHandlerChoices)
	assert.NotEmpty(t, settings.SummarizationHandlerChoices)
	assert.NotEmpty(t, settings.NotificationHandlerChoices)
	assert.Equal(t, false, settings.UpdateStatus)
	assert.Empty(t, settings.UpdateException)

	/* Test Settings Defaults */

	var s = settings.Settings
	assert.Equal(t, "forest", s.Theme)
	assert.Equal(t, true, s.SendNotification)
	assert.Equal(t, 5, s.RefreshInterval)
	assert.Equal(t, 238, s.ReadingSpeed)
	assert.Equal(t, 36, s.RecentHours)
	assert.IsType(t, true, s.FinishedOnboarding)

	assert.Contains(t, settings.NotificationHandlerChoices, s.NotificationHandlerKey)
	assert.Contains(t, settings.SummarizationHandlerChoices, s.SummarizationHandlerKey)
	assert.Contains(t, settings.ContentHandlerChoices, s.ContentRetrievalHandlerKey)
}

func TestOnboarding(t *testing.T) {
	req, err := http.NewRequest("GET", baseURL+"/onboarding/", nil)
	req.Header.Set("accept", "application/json")

	if err != nil {
		t.Fatal(err)
	}

	res, err := client.Do(req)
	if err != nil {
		t.Fatal(err)
	}

	if res.StatusCode != http.StatusOK {
		t.Errorf("Onboarding page returned status code %d, expected %d", res.StatusCode, http.StatusOK)
	}

	var onboarding OnboardingResponse

	if err := json.NewDecoder(res.Body).Decode(&onboarding); err != nil {
		t.Fatal(err)
	}

	defer res.Body.Close()

	assert.NotEmpty(t, onboarding.Settings)
}

func TestHandlerSettings(t *testing.T) {
	req, err := http.Get(baseURL + "/util/list-handlers")
	if err != nil {
		t.Fatal(err)
	}

	var handlers []Handler

	if err := json.NewDecoder(req.Body).Decode(&handlers); err != nil {
		t.Fatal(err)
	}

	for _, handler := range handlers {
		req, err := http.NewRequest("GET", baseURL+"/settings/"+handler.Name, nil)
		req.Header.Set("accept", "application/json")

		if err != nil {
			t.Fatal(err)
		}

		res, err := client.Do(req)
		if err != nil {
			t.Fatal(err)
		}

		var requestedHandler HandlerSettingsResponse

		if err := json.NewDecoder(res.Body).Decode(&requestedHandler); err != nil {
			t.Fatal(err)
		}

		defer res.Body.Close()

		assert.NotEmpty(t, requestedHandler.Settings)
		assert.NotEmpty(t, requestedHandler.Schema)
		assert.Equal(t, requestedHandler.Handler.Type, handler.Name)
	}

}

func TestReadEntry(t *testing.T) {
	req, err := http.Get(baseURL + "/util/list-feed-entries")
	if err != nil {
		t.Fatal(err)
	}

	var entries []FeedEntry

	if err := json.NewDecoder(req.Body).Decode(&entries); err != nil {
		t.Fatal(err)
	}

	for _, entry := range entries {
		req, err := http.NewRequest("GET", baseURL+"/read/"+entry.Id, nil)
		req.Header.Set("accept", "application/json")

		if err != nil {
			t.Fatal(err)
		}

		res, err := client.Do(req)
		if err != nil {
			t.Fatal(err)
		}

		var feedEntry ReadFeedEntryResponse

		if err := json.NewDecoder(res.Body).Decode(&feedEntry); err != nil {
			t.Fatal(err)
		}

		defer res.Body.Close()

		requestedEntry := feedEntry.Content

		assert.Equal(t, entry.Id, requestedEntry.Id)
		assert.NotEmpty(t, requestedEntry.FeedID)
		assert.NotEmpty(t, requestedEntry.FeedName)
		assert.NotEmpty(t, requestedEntry.Title)
		assert.NotEmpty(t, requestedEntry.URL)
	}

}

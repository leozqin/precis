/*
These tests enumerate entities and then check to see if they're reachable
*/

package precis_test

import (
	"encoding/json"
	"net/http"
	"testing"
)

func TestFeedPage(t *testing.T) {
	req, err := http.Get(baseURL + "/util/list-feeds")
	if err != nil {
		t.Fatal(err)
	}

	var feeds []Feed

	if err := json.NewDecoder(req.Body).Decode(&feeds); err != nil {
		t.Fatal(err)
	}

	for _, feed := range feeds {
		req, err := http.Get(baseURL + "/feeds/" + feed.Id)
		if err != nil {
			t.Fatal(err)
		}

		if req.StatusCode != http.StatusOK {
			t.Errorf("Feed page for feed %s returned status code %d, expected %d", feed.Name, req.StatusCode, http.StatusOK)
		}
	}
}

func TestReadPage(t *testing.T) {
	req, err := http.Get(baseURL + "/util/list-feed-entries")
	if err != nil {
		t.Fatal(err)
	}

	var entries []FeedEntry

	if err := json.NewDecoder(req.Body).Decode(&entries); err != nil {
		t.Fatal(err)
	}

	for _, entry := range entries {
		req, err := http.Get(baseURL + "/read/" + entry.Id)
		if err != nil {
			t.Fatal(err)
		}

		if req.StatusCode != http.StatusOK {
			t.Errorf("Read page for feed entry %s returned status code %d, expected %d", entry.Title, req.StatusCode, http.StatusOK)
		}
	}
}

func TestHandlerConfigPage(t *testing.T) {
	req, err := http.Get(baseURL + "/util/list-handlers")
	if err != nil {
		t.Fatal(err)
	}

	var handlers []Handler

	if err := json.NewDecoder(req.Body).Decode(&handlers); err != nil {
		t.Fatal(err)
	}

	for _, handler := range handlers {
		req, err := http.Get(baseURL + "/settings/" + handler.Name)
		if err != nil {
			t.Fatal(err)
		}

		if req.StatusCode != http.StatusOK {
			t.Errorf("Handler config page for handler %s returned status code %d, expected %d", handler.Name, req.StatusCode, http.StatusOK)
		}
	}
}

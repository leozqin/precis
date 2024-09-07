/*
These tests check to see if static pages are reachable
*/

package precis_test

import (
	"net/http"
	"os"
	"testing"
)

var baseURL = os.Getenv("RSS_BASE_URL")

func TestHomePage(t *testing.T) {
	// Create a new HTTP request to the home page.
	req, err := http.Get(baseURL + "/")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("Home page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

func TestSettingsPage(t *testing.T) {
	req, err := http.Get(baseURL + "/settings")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("Settings page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

func TestFeedsPage(t *testing.T) {
	req, err := http.Get(baseURL + "/feeds")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("Feeds page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

func TestNewFeedsPage(t *testing.T) {
	req, err := http.Get(baseURL + "/feeds/new/")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("New feeds page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

func TestAboutPage(t *testing.T) {
	req, err := http.Get(baseURL + "/about")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("About page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

func TestRecentPage(t *testing.T) {
	req, err := http.Get(baseURL + "/recent")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("Recent page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

func TestOnboardingPage(t *testing.T) {
	req, err := http.Get(baseURL + "/onboarding")
	if err != nil {
		t.Fatal(err)
	}

	if req.StatusCode != http.StatusOK {
		t.Errorf("Onboarding page returned status code %d, expected %d", req.StatusCode, http.StatusOK)
	}
}

package main

import (
	"encoding/json"
	"testing"
)

func number(s string) json.Number { return json.Number(s) }

func TestMatches(t *testing.T) {
	cases := []struct {
		got, want any
		tolerance string
		ok        bool
	}{
		{number("1.29"), 1.28, "0.01", true},
		{number("1.30"), 1.28, "0.01", false},
		{number("1.27"), 1.28, "0.01", true},
		{number("12"), 12.0, "", true},
		{number("12.5"), 12.0, "", false},
		{"12", 12.0, "1", false},
		{nil, nil, "", true},
		{number("0"), nil, "0.01", false},
		{"caution", "caution", "", true},
		{"none", "caution", "", false},
		{true, true, "", true},
	}
	for _, c := range cases {
		if got := matches(c.got, c.want, c.tolerance); got != c.ok {
			t.Errorf("matches(%v, %v, %q) = %v, want %v", c.got, c.want, c.tolerance, got, c.ok)
		}
	}
}

func TestJudgeErrors(t *testing.T) {
	c := testCase{ID: "invalid-1", Expected: map[string]any{"error": "outOfRange"}}
	if p := judge(c, answer{Error: "outOfRange"}, nil); len(p) != 0 {
		t.Errorf("right error judged wrong: %v", p)
	}
	if p := judge(c, answer{Output: map[string]any{}}, nil); len(p) != 1 {
		t.Errorf("a result where an error was expected passed")
	}
	c = testCase{ID: "a", Expected: map[string]any{"decimalYear": 2028.1612021858}}
	if p := judge(c, answer{Error: "outOfRange"}, nil); len(p) != 1 {
		t.Errorf("an error where a result was expected passed")
	}
	if p := judge(c, answer{Output: map[string]any{}}, map[string]string{"decimalYear": "0.0001"}); len(p) != 1 {
		t.Errorf("a missing field passed")
	}
}

func TestValidate(t *testing.T) {
	v := vectors{
		Operations: []operation{{ID: "decimalYear", Inputs: []string{"date"}, Outputs: []string{"decimalYear"}}},
		Fields:     map[string]any{"date": "", "decimalYear": ""},
		Cases: []testCase{{ID: "a", Operation: "decimalYear",
			Input: map[string]json.RawMessage{"date": json.RawMessage(`"2028-02-29"`)}, Expected: map[string]any{"latitudeInDegrees": 1.0}}},
	}
	if validate(v) == nil {
		t.Error("an output the operation doesn't have passed validation")
	}
}

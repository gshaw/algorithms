// algorithms-check runs an implementation over the test data on algorithms.gshaw.ca,
// judges each result against the file's tolerances and writes conformance.json.
// The contract it checks is on https://algorithms.gshaw.ca/format/#implementations.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"math"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

var version = "dev"

const defaultSource = "https://algorithms.gshaw.ca/algorithms.json"

type operation struct {
	ID      string   `json:"id"`
	Inputs  []string `json:"inputs"`
	Outputs []string `json:"outputs"`
}

type testCase struct {
	ID        string                     `json:"id"`
	Operation string                     `json:"operation"`
	Input     map[string]json.RawMessage `json:"input"`
	Expected  map[string]any             `json:"expected"`
}

type vectors struct {
	Algorithm     string            `json:"algorithm"`
	Placeholder   string            `json:"placeholder"`
	PublishedDate string            `json:"publishedDate"`
	Operations    []operation       `json:"operations"`
	Fields        map[string]any    `json:"fields"`
	Tolerances    map[string]string `json:"tolerances"`
	Cases         []testCase        `json:"cases"`
}

// result is one algorithm's line in conformance.json.
type result struct {
	Status         string `json:"status"`
	PublishedDate  string `json:"publishedDate"`
	Cases          int    `json:"cases"`
	Passed         int    `json:"passed"`
	Failed         int    `json:"failed"`
	NotImplemented int    `json:"notImplemented"`
}

type conformance struct {
	Checker string            `json:"checker"`
	Source  string            `json:"source"`
	Results map[string]result `json:"results"`
}

func main() {
	os.Exit(run())
}

func run() int {
	source := flag.String("source", defaultSource, "algorithms.json URL, or a directory of test files")
	only := flag.String("only", "", "comma-separated algorithm slugs to check, like wmm")
	out := flag.String("out", "conformance.json", "where to write the results; empty to skip")
	quiet := flag.Bool("quiet", false, "print only failures and each algorithm's result")
	timeout := flag.Duration("timeout", 10*time.Minute, "how long one algorithm's run may take")
	showVersion := flag.Bool("version", false, "print the version")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: algorithms-check [flags] [-- command...]\n\n")
		fmt.Fprintf(os.Stderr, "Runs command (default: mise run evaluate) once per algorithm, with its cases\n")
		fmt.Fprintf(os.Stderr, "as JSON Lines on standard input, and judges what it writes back.\n\n")
		flag.PrintDefaults()
	}
	flag.Parse()
	if *showVersion {
		fmt.Println(version)
		return 0
	}
	command := flag.Args()
	if len(command) == 0 {
		command = []string{"mise", "run", "evaluate"}
	}

	files, err := load(*source)
	if err != nil {
		fmt.Fprintln(os.Stderr, "algorithms-check:", err)
		return 2
	}
	wanted := map[string]bool{}
	for _, slug := range strings.Split(*only, ",") {
		if slug = strings.TrimSpace(slug); slug != "" {
			wanted[slug] = true
		}
	}

	report := conformance{Checker: version, Source: *source, Results: map[string]result{}}
	anyFailed := false
	for _, v := range files {
		if len(wanted) > 0 && !wanted[v.Algorithm] {
			continue
		}
		if v.Placeholder != "" {
			if !*quiet {
				fmt.Printf("%s: skipped, its test data is a placeholder\n", v.Algorithm)
			}
			continue
		}
		if err := validate(v); err != nil {
			fmt.Fprintf(os.Stderr, "algorithms-check: %s: %v\n", v.Algorithm, err)
			return 2
		}
		r, err := check(v, command, *timeout, *quiet)
		if err != nil {
			fmt.Fprintf(os.Stderr, "algorithms-check: %s: %v\n", v.Algorithm, err)
			return 2
		}
		report.Results[v.Algorithm] = r
		anyFailed = anyFailed || r.Status == "fails"
		fmt.Printf("%s: %s, %d of %d passed", v.Algorithm, r.Status, r.Passed, r.Cases)
		if r.NotImplemented > 0 {
			fmt.Printf(", %d not implemented", r.NotImplemented)
		}
		fmt.Println()
	}
	if len(wanted) > 0 {
		for slug := range wanted {
			if _, ok := report.Results[slug]; !ok {
				fmt.Fprintf(os.Stderr, "algorithms-check: no published test data for %s\n", slug)
				return 2
			}
		}
	}

	if *out != "" {
		data, _ := json.MarshalIndent(report, "", "  ")
		if err := os.WriteFile(*out, append(data, '\n'), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, "algorithms-check:", err)
			return 2
		}
	}
	if anyFailed {
		return 1
	}
	return 0
}

// load reads every test file from algorithms.json at a URL, or every *.json in a directory.
func load(source string) ([]vectors, error) {
	var files []vectors
	if strings.HasPrefix(source, "http://") || strings.HasPrefix(source, "https://") {
		var list []struct {
			Slug    string `json:"slug"`
			Vectors string `json:"vectors"`
		}
		if err := fetchJSON(source, &list); err != nil {
			return nil, err
		}
		for _, entry := range list {
			var v vectors
			if err := fetchJSON(entry.Vectors, &v); err != nil {
				return nil, err
			}
			files = append(files, v)
		}
		return files, nil
	}
	paths, err := filepath.Glob(filepath.Join(source, "*.json"))
	if err != nil {
		return nil, err
	}
	if len(paths) == 0 {
		return nil, fmt.Errorf("no test files in %s", source)
	}
	sort.Strings(paths)
	for _, path := range paths {
		data, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		var v vectors
		if err := json.Unmarshal(data, &v); err != nil {
			return nil, fmt.Errorf("%s: %w", path, err)
		}
		files = append(files, v)
	}
	return files, nil
}

func fetchJSON(url string, into any) error {
	client := http.Client{Timeout: time.Minute}
	response, err := client.Get(url)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return fmt.Errorf("%s: %s", url, response.Status)
	}
	if err := json.NewDecoder(response.Body).Decode(into); err != nil {
		return fmt.Errorf("%s: %w", url, err)
	}
	return nil
}

// validate rejects a file whose cases use a field their operation doesn't have.
func validate(v vectors) error {
	operations := map[string]operation{}
	for _, op := range v.Operations {
		operations[op.ID] = op
	}
	for name, tolerance := range v.Tolerances {
		if _, ok := v.Fields[name]; !ok {
			return fmt.Errorf("tolerance for unknown field %s", name)
		}
		if _, err := strconv.ParseFloat(tolerance, 64); err != nil {
			return fmt.Errorf("tolerance for %s isn't a number: %q", name, tolerance)
		}
	}
	seen := map[string]bool{}
	for _, c := range v.Cases {
		if seen[c.ID] {
			return fmt.Errorf("case id %s used twice", c.ID)
		}
		seen[c.ID] = true
		op, ok := operations[c.Operation]
		if !ok {
			return fmt.Errorf("case %s: unknown operation %s", c.ID, c.Operation)
		}
		for name := range c.Input {
			if !contains(op.Inputs, name) {
				return fmt.Errorf("case %s: %s isn't an input of %s", c.ID, name, op.ID)
			}
		}
		for name := range c.Expected {
			if name != "error" && !contains(op.Outputs, name) {
				return fmt.Errorf("case %s: %s isn't an output of %s", c.ID, name, op.ID)
			}
		}
	}
	return nil
}

func contains(list []string, s string) bool {
	for _, item := range list {
		if item == s {
			return true
		}
	}
	return false
}

type answer struct {
	ID     string         `json:"id"`
	Output map[string]any `json:"output"`
	Error  string         `json:"error"`
}

// check runs the command once over every case in v and judges the answers.
func check(v vectors, command []string, timeout time.Duration, quiet bool) (result, error) {
	var input bytes.Buffer
	for _, c := range v.Cases {
		line, _ := json.Marshal(map[string]any{
			"algorithm": v.Algorithm, "id": c.ID, "operation": c.Operation, "input": c.Input,
		})
		input.Write(line)
		input.WriteByte('\n')
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, command[0], command[1:]...)
	cmd.Stdin = &input
	cmd.Stderr = os.Stderr
	stdout, err := cmd.Output()
	if ctx.Err() != nil {
		return result{}, fmt.Errorf("%s took longer than %s", strings.Join(command, " "), timeout)
	}
	var exitErr *exec.ExitError
	if err != nil && !errors.As(err, &exitErr) {
		return result{}, err
	}
	if err != nil {
		return result{}, fmt.Errorf("%s exited with %d", strings.Join(command, " "), exitErr.ExitCode())
	}

	answers, err := parseAnswers(stdout)
	if err != nil {
		return result{}, err
	}

	r := result{PublishedDate: v.PublishedDate, Cases: len(v.Cases)}
	for _, c := range v.Cases {
		a, ok := answers[c.ID]
		var problems []string
		switch {
		case !ok:
			problems = []string{"no answer"}
		case a.Error == "notImplemented":
			r.NotImplemented++
			if !quiet {
				fmt.Printf("  – %s  not implemented\n", c.ID)
			}
			continue
		default:
			problems = judge(c, a, v.Tolerances)
		}
		if len(problems) == 0 {
			r.Passed++
			if !quiet {
				fmt.Printf("  ✓ %s\n", c.ID)
			}
			continue
		}
		r.Failed++
		fmt.Printf("  ✗ %s  %s\n", c.ID, strings.Join(problems, "; "))
	}
	switch {
	case r.Failed > 0:
		r.Status = "fails"
	case r.NotImplemented > 0:
		r.Status = "incomplete"
	default:
		r.Status = "passes"
	}
	return r, nil
}

func parseAnswers(stdout []byte) (map[string]answer, error) {
	answers := map[string]answer{}
	scanner := bufio.NewScanner(bytes.NewReader(stdout))
	scanner.Buffer(make([]byte, 1024*1024), 16*1024*1024)
	for n := 1; scanner.Scan(); n++ {
		line := bytes.TrimSpace(scanner.Bytes())
		if len(line) == 0 {
			continue
		}
		var a answer
		decoder := json.NewDecoder(bytes.NewReader(line))
		decoder.UseNumber()
		if err := decoder.Decode(&a); err != nil || a.ID == "" {
			return nil, fmt.Errorf("output line %d isn't a result: %.200s", n, line)
		}
		answers[a.ID] = a
	}
	return answers, scanner.Err()
}

// judge compares only the fields in expected: numbers with a tolerance within it,
// everything else exactly.
func judge(c testCase, a answer, tolerances map[string]string) []string {
	var problems []string
	if want, ok := c.Expected["error"]; ok {
		if a.Error != want {
			got := a.Error
			if got == "" {
				got = "a result"
			}
			problems = append(problems, fmt.Sprintf("error %s, expected %v", got, want))
		}
		return problems
	}
	if a.Error != "" {
		return []string{"error " + a.Error}
	}
	names := make([]string, 0, len(c.Expected))
	for name := range c.Expected {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		want := c.Expected[name]
		got, ok := a.Output[name]
		if !ok {
			problems = append(problems, name+" missing")
			continue
		}
		if !matches(got, want, tolerances[name]) {
			message := fmt.Sprintf("%s %v, expected %v", name, show(got), show(want))
			if tolerances[name] != "" {
				message += " ± " + tolerances[name]
			}
			problems = append(problems, message)
		}
	}
	return problems
}

func matches(got, want any, tolerance string) bool {
	wantNumber, wantIsNumber := want.(float64)
	if !wantIsNumber {
		return got == want
	}
	number, ok := got.(json.Number)
	if !ok {
		return false
	}
	gotNumber, err := number.Float64()
	if err != nil {
		return false
	}
	if tolerance == "" {
		return gotNumber == wantNumber
	}
	limit, _ := strconv.ParseFloat(tolerance, 64)
	// A hair of slack so a value exactly at the tolerance isn't lost to binary rounding.
	return math.Abs(gotNumber-wantNumber) <= limit*(1+1e-9)
}

func show(value any) string {
	if value == nil {
		return "null"
	}
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Sprint(value)
	}
	return string(data)
}

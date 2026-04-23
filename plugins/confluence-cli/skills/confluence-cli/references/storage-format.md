# Confluence storage format — cheatsheet

Storage format is Confluence's XHTML-subset serialization. It's the format returned by `get-page --body-format storage` and the one accepted by `create-page` / `update-page` when `--representation storage` (default).

## Basics

```xml
<h1>Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>
<p>Paragraph text. Use <strong>bold</strong>, <em>italic</em>, <u>underline</u>.</p>
<p><code>inline code</code> for short snippets.</p>
<hr />                                <!-- horizontal rule -->
```

**Escape** `<`, `>`, `&` in text content. `<br />`, `<hr />` are self-closing.

## Lists

```xml
<ul>
  <li>first</li>
  <li>second
    <ul>
      <li>nested</li>
    </ul>
  </li>
</ul>

<ol>
  <li>step one</li>
  <li>step two</li>
</ol>
```

## Tables

```xml
<table>
  <tbody>
    <tr>
      <th>Column A</th>
      <th>Column B</th>
    </tr>
    <tr>
      <td>cell 1</td>
      <td>cell 2</td>
    </tr>
  </tbody>
</table>
```

`<th>` cells in the first row render as styled headers. Tables can contain any storage markup in cells, including code blocks.

## Code blocks (with syntax highlighting)

```xml
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">php</ac:parameter>
  <ac:parameter ac:name="title">Optional title</ac:parameter>
  <ac:parameter ac:name="linenumbers">true</ac:parameter>
  <ac:plain-text-body><![CDATA[
<?php
echo "hello";
]]></ac:plain-text-body>
</ac:structured-macro>
```

Supported languages include `php`, `java`, `python`, `js`, `ts`, `bash`, `sql`, `yaml`, `json`, `xml`, `html`, `css`, `ruby`, `go`, `rust`, `kotlin`, `csharp`, `cpp`, `scala`, `perl`, `powershell`, `plain`. Use CDATA to avoid escaping.

## Panels (info / note / warning / tip)

```xml
<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:parameter ac:name="title">Title</ac:parameter>
  <ac:rich-text-body>
    <p>Body content with <strong>markup</strong>.</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

Swap `info` with: `note` (yellow), `warning` (red), `tip` (green), `panel` (neutral, custom color).

## Expand / collapse

```xml
<ac:structured-macro ac:name="expand" ac:schema-version="1">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body>
    <p>Hidden content</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

## Table of contents

```xml
<ac:structured-macro ac:name="toc" ac:schema-version="1">
  <ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>
```

Usually placed right after the H1 / at the top of a long page.

## Links

### External

```xml
<a href="https://example.com">text</a>
```

### To another Confluence page (by title in the same space)

```xml
<ac:link>
  <ri:page ri:content-title="Target page title" />
  <ac:plain-text-link-body><![CDATA[custom link text]]></ac:plain-text-link-body>
</ac:link>
```

### Cross-space link

```xml
<ac:link>
  <ri:page ri:space-key="CS" ri:content-title="Target title" />
</ac:link>
```

### Anchor on current page

```xml
<ac:link ac:anchor="section-heading"><ac:plain-text-link-body><![CDATA[jump]]></ac:plain-text-link-body></ac:link>
```

## Images (from attachments)

Upload first with `upload-attachment <pageId> <path>`, then embed:

```xml
<ac:image>
  <ri:attachment ri:filename="diagram.png" />
</ac:image>
```

### Sized / aligned

```xml
<ac:image ac:width="600" ac:align="center" ac:alt="architecture diagram">
  <ri:attachment ri:filename="diagram.png" />
</ac:image>
```

### External image

```xml
<ac:image ac:width="400">
  <ri:url ri:value="https://example.com/image.png" />
</ac:image>
```

## Mentions

```xml
<ac:link><ri:user ri:account-id="712020:xxxx-xxxx" /></ac:link>
```

Account IDs are visible in the user JSON returned by `whoami`.

## Task list

```xml
<ac:task-list>
  <ac:task>
    <ac:task-id>1</ac:task-id>
    <ac:task-status>incomplete</ac:task-status>
    <ac:task-body><span>Write tests</span></ac:task-body>
  </ac:task>
  <ac:task>
    <ac:task-id>2</ac:task-id>
    <ac:task-status>complete</ac:task-status>
    <ac:task-body><span>Merge PR</span></ac:task-body>
  </ac:task>
</ac:task-list>
```

## Status badge

```xml
<ac:structured-macro ac:name="status" ac:schema-version="1">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">DONE</ac:parameter>
</ac:structured-macro>
```

Colours: `Green`, `Yellow`, `Red`, `Blue`, `Grey`.

## Dates

```xml
<time datetime="2026-04-23" />
```

Renders as a localized date pill.

## Jira issue link

```xml
<ac:structured-macro ac:name="jira" ac:schema-version="1">
  <ac:parameter ac:name="key">CZDEV-1234</ac:parameter>
</ac:structured-macro>
```

Renders with live status from Jira.

## Common gotchas

- **CDATA is required** inside code blocks if the content contains `<`, `>`, `&`, or XML-like syntax.
- **Self-close empty elements**: `<br/>`, `<hr/>`, `<ac:image ... />` (when it has no body). Non-self-closed empty `<ac:image>` can fail validation.
- **XML, not HTML**: attribute values need double quotes, tags must be balanced. No `<br>` without `/`.
- **Nested macros**: most macros allow `<ac:rich-text-body>` which contains storage markup. Exception: `<ac:plain-text-body>` accepts only text (wrap in CDATA).
- **Unicode**: works fine; use UTF-8.
- **Title collision**: two pages in the same space can't have the same title. `create-page` fails with HTTP 409.
- **Large bodies**: keep under ~5 MB; for huge content split into multiple pages linked from a parent index.

## Converting from Markdown

Rough mapping:

| Markdown | Storage format |
|---|---|
| `# H1` | `<h1>` |
| `**bold**` | `<strong>` |
| `*italic*` | `<em>` |
| `` `code` `` | `<code>` |
| ` ```lang\n...\n``` ` | `<ac:structured-macro ac:name="code">...CDATA...` |
| `- item` | `<ul><li>` |
| `1. item` | `<ol><li>` |
| `[text](url)` | `<a href="url">text</a>` |
| `> quote` | `<blockquote><p>...</p></blockquote>` |
| `\| a \| b \|` table | `<table><tbody><tr><td>` |

If `pandoc` is installed: `pandoc input.md -f gfm -t html` gives a reasonable starting point; wrap fenced code blocks in the `code` macro manually for syntax highlighting.

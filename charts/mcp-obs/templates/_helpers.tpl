{{/*
Common template helpers for mcp-obs chart
*/}}

{{- define "mcp-obs.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "mcp-obs.fullname" -}}
{{ printf "%s-%s" .Release.Name (include "mcp-obs.name" .) }}
{{- end -}}

{{- define "mcp-obs.labels" -}}
app.kubernetes.io/name: {{ include "mcp-obs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "mcp-obs.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mcp-obs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}} 
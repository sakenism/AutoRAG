# Complete Ollama Helm Chart with Auto-Scaling

## Helm Chart Structure

```
ollama-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── configmap.yaml
│   ├── service.yaml
│   ├── servicemonitor.yaml
│   ├── statefulset.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── NOTES.txt
└── README.md
```

---

## Chart.yaml

```yaml
apiVersion: v2
name: ollama
description: A Helm chart for deploying Ollama with auto-scaling capabilities
type: application
version: 1.0.0
appVersion: "latest"
home: https://ollama.com
sources:
  - https://github.com/ollama/ollama
keywords:
  - ai
  - llm
  - machine-learning
  - ollama
maintainers:
  - name: Ollama Team
    email: support@ollama.com
dependencies:
  - name: prometheus
    version: "25.8.0"
    repository: "https://prometheus-community.github.io/helm-charts"
    condition: prometheus.enabled
```

---

## values.yaml

```yaml
# Global settings
global:
  imageRegistry: ""
  storageClass: ""

# Image configuration
image:
  registry: docker.io
  repository: ollama/ollama
  tag: "latest"
  pullPolicy: IfNotPresent
  pullSecrets: []

# Deployment configuration
replicaCount: 3
nameOverride: ""
fullnameOverride: ""

# Service account
serviceAccount:
  create: true
  automount: true
  annotations: {}
  name: ""

# Pod security context
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000

# Container security context
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
  capabilities:
    drop:
    - ALL

# Ollama specific configuration
ollama:
  # Environment variables
  env:
    OLLAMA_HOST: "0.0.0.0:11434"
    OLLAMA_FLASH_ATTENTION: "1"
    OLLAMA_KEEP_ALIVE: "-1"
    OLLAMA_MAX_LOADED_MODELS: "1"
    OLLAMA_NUM_PARALLEL: "4"
    OLLAMA_MAX_QUEUE: "512"
    OLLAMA_KV_CACHE_TYPE: "q8_0"
    OLLAMA_DEBUG: "false"
    OLLAMA_ORIGINS: "*"
  
  # GPU configuration
  gpu:
    enabled: true
    type: nvidia  # nvidia, amd, or intel
    count: 1
    
  # Models to pre-load
  models:
    preload:
      - llama3.2:3b
      - codellama:7b
    # Models to create with custom settings
    create: []
    # Example:
    # - name: llama3-custom
    #   from: llama3.2:3b
    #   template: |
    #     FROM llama3.2:3b
    #     PARAMETER num_ctx 4096

# Resource configuration
resources:
  requests:
    memory: "8Gi"
    cpu: "2"
    nvidia.com/gpu: 1
  limits:
    memory: "16Gi"
    cpu: "4"
    nvidia.com/gpu: 1

# Node selection
nodeSelector:
  nvidia.com/gpu.present: "true"

tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule

affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: node-type
          operator: In
          values:
          - gpu

# Persistence
persistence:
  enabled: true
  storageClass: ""
  accessMode: ReadWriteOnce
  size: 100Gi
  annotations: {}

# Service configuration
service:
  type: ClusterIP
  port: 11434
  targetPort: 11434
  annotations: {}

# Metrics and monitoring
metrics:
  enabled: true
  port: 9090
  path: /metrics
  serviceMonitor:
    enabled: true
    interval: 15s
    scrapeTimeout: 10s
    additionalLabels: {}

# Auto-scaling configuration
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  
  # Metrics for scaling decisions
  metrics:
    cpu:
      enabled: true
      targetAverageUtilization: 70
    memory:
      enabled: true
      targetAverageUtilization: 80
    queueLength:
      enabled: true
      targetAverageValue: 10
      metricName: ollama_request_queue_length
    responseTime:
      enabled: false
      targetAverageValue: 5
      metricName: ollama_avg_response_time_seconds
    
  # Scaling behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 3
        periodSeconds: 60
      - type: Percent
        value: 50
        periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 180
      selectPolicy: Min

# Pod Disruption Budget
podDisruptionBudget:
  enabled: true
  minAvailable: 2

# Ingress configuration
ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: ollama.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

# Health checks
livenessProbe:
  enabled: true
  httpGet:
    path: /
    port: 11434
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  enabled: true
  httpGet:
    path: /api/tags
    port: 11434
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

# Prometheus configuration (for custom metrics)
prometheus:
  enabled: false
  server:
    persistentVolume:
      enabled: false

# Custom metrics adapter (required for queue length scaling)
customMetricsAdapter:
  enabled: true
  image:
    repository: k8s.gcr.io/prometheus-adapter/prometheus-adapter
    tag: v0.11.2
  prometheus:
    url: http://prometheus-server.monitoring.svc.cluster.local
    port: 80

# Additional labels
labels: {}

# Additional annotations
annotations: {}

# Pod annotations
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
  prometheus.io/path: "/metrics"

# Extra environment variables
extraEnvVars: []

# Extra volumes
extraVolumes: []

# Extra volume mounts
extraVolumeMounts: []

# Init containers
initContainers: []
```

---

## templates/_helpers.tpl

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "ollama.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ollama.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ollama.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ollama.labels" -}}
helm.sh/chart: {{ include "ollama.chart" . }}
{{ include "ollama.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ollama.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ollama.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ollama.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ollama.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
GPU resource configuration
*/}}
{{- define "ollama.gpuResources" -}}
{{- if .Values.ollama.gpu.enabled }}
{{- if eq .Values.ollama.gpu.type "nvidia" }}
nvidia.com/gpu: {{ .Values.ollama.gpu.count }}
{{- else if eq .Values.ollama.gpu.type "amd" }}
amd.com/gpu: {{ .Values.ollama.gpu.count }}
{{- else if eq .Values.ollama.gpu.type "intel" }}
gpu.intel.com/i915: {{ .Values.ollama.gpu.count }}
{{- end }}
{{- end }}
{{- end }}
```

---

## templates/configmap.yaml

```yaml
{{- if .Values.ollama.models.preload }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ollama.fullname" . }}-scripts
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
data:
  preload-models.sh: |
    #!/bin/bash
    set -e
    
    echo "Starting Ollama server in background..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready
    echo "Waiting for Ollama to be ready..."
    while ! curl -f http://localhost:11434/ >/dev/null 2>&1; do
      sleep 2
    done
    
    echo "Ollama is ready, preloading models..."
    
    {{- range .Values.ollama.models.preload }}
    echo "Pulling model: {{ . }}"
    ollama pull {{ . }}
    echo "Prewarming model: {{ . }}"
    echo "Hello" | ollama run {{ . }} --no-stream >/dev/null
    {{- end }}
    
    {{- range .Values.ollama.models.create }}
    echo "Creating custom model: {{ .name }}"
    cat > /tmp/{{ .name }}.modelfile << 'EOF'
{{ .template }}
EOF
    ollama create {{ .name }} -f /tmp/{{ .name }}.modelfile
    {{- end }}
    
    echo "All models preloaded successfully!"
    
    # Keep Ollama running
    wait $OLLAMA_PID
    
  metrics-exporter.py: |
    #!/usr/bin/env python3
    import time
    import json
    import requests
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
    
    class OllamaMetrics:
        def __init__(self):
            self.queue_length = 0
            self.response_times = []
            self.active_requests = 0
            
        def update_queue_length(self, length):
            self.queue_length = length
            
        def add_response_time(self, time_seconds):
            self.response_times.append(time_seconds)
            if len(self.response_times) > 100:  # Keep last 100 measurements
                self.response_times.pop(0)
                
        def get_avg_response_time(self):
            if not self.response_times:
                return 0
            return sum(self.response_times) / len(self.response_times)
    
    metrics = OllamaMetrics()
    
    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/metrics':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                
                metrics_text = f"""# HELP ollama_request_queue_length Current request queue length
# TYPE ollama_request_queue_length gauge
ollama_request_queue_length {metrics.queue_length}

# HELP ollama_avg_response_time_seconds Average response time in seconds
# TYPE ollama_avg_response_time_seconds gauge
ollama_avg_response_time_seconds {metrics.get_avg_response_time()}

# HELP ollama_active_requests Number of currently active requests
# TYPE ollama_active_requests gauge
ollama_active_requests {metrics.active_requests}
"""
                self.wfile.write(metrics_text.encode())
            else:
                self.send_response(404)
                self.end_headers()
    
    def monitor_ollama():
        while True:
            try:
                # Monitor Ollama status
                response = requests.get('http://localhost:11434/api/ps', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Extract queue information if available
                    # This is a placeholder - actual implementation depends on Ollama API
                    pass
            except Exception as e:
                print(f"Error monitoring Ollama: {e}")
            time.sleep(15)
    
    if __name__ == '__main__':
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_ollama, daemon=True)
        monitor_thread.start()
        
        # Start metrics server
        server = HTTPServer(('0.0.0.0', 9090), MetricsHandler)
        print("Metrics server started on port 9090")
        server.serve_forever()
{{- end }}
```

---

## templates/statefulset.yaml

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "ollama.fullname" . }}
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
    {{- with .Values.labels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  {{- with .Values.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  serviceName: {{ include "ollama.fullname" . }}-headless
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "ollama.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "ollama.selectorLabels" . | nindent 8 }}
        {{- with .Values.labels }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      annotations:
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
    spec:
      serviceAccountName: {{ include "ollama.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      {{- with .Values.image.pullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- if .Values.initContainers }}
      initContainers:
        {{- toYaml .Values.initContainers | nindent 8 }}
      {{- end }}
      containers:
      - name: ollama
        image: "{{ .Values.image.registry }}/{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 11434
          protocol: TCP
        {{- if .Values.metrics.enabled }}
        - name: metrics
          containerPort: {{ .Values.metrics.port }}
          protocol: TCP
        {{- end }}
        env:
        {{- range $key, $value := .Values.ollama.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        {{- if .Values.ollama.gpu.enabled }}
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        {{- end }}
        {{- with .Values.extraEnvVars }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
        resources:
          requests:
            memory: {{ .Values.resources.requests.memory }}
            cpu: {{ .Values.resources.requests.cpu }}
            {{- include "ollama.gpuResources" . | nindent 12 }}
          limits:
            memory: {{ .Values.resources.limits.memory }}
            cpu: {{ .Values.resources.limits.cpu }}
            {{- include "ollama.gpuResources" . | nindent 12 }}
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
        {{- if .Values.ollama.models.preload }}
        - name: scripts
          mountPath: /scripts
        {{- end }}
        {{- with .Values.extraVolumeMounts }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
        {{- if .Values.livenessProbe.enabled }}
        livenessProbe:
          {{- omit .Values.livenessProbe "enabled" | toYaml | nindent 10 }}
        {{- end }}
        {{- if .Values.readinessProbe.enabled }}
        readinessProbe:
          {{- omit .Values.readinessProbe "enabled" | toYaml | nindent 10 }}
        {{- end }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 10 }}
        {{- if .Values.ollama.models.preload }}
        command: ["/bin/bash", "/scripts/preload-models.sh"]
        {{- end }}
      
      {{- if .Values.metrics.enabled }}
      - name: metrics-exporter
        image: python:3.9-slim
        ports:
        - name: metrics
          containerPort: 9090
          protocol: TCP
        command: ["/bin/bash", "-c"]
        args:
        - |
          pip install requests
          python /scripts/metrics-exporter.py
        volumeMounts:
        - name: scripts
          mountPath: /scripts
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      {{- end }}
      
      volumes:
      {{- if .Values.ollama.models.preload }}
      - name: scripts
        configMap:
          name: {{ include "ollama.fullname" . }}-scripts
          defaultMode: 0755
      {{- end }}
      {{- with .Values.extraVolumes }}
      {{- toYaml . | nindent 6 }}
      {{- end }}
      
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
  
  {{- if .Values.persistence.enabled }}
  volumeClaimTemplates:
  - metadata:
      name: ollama-data
      {{- with .Values.persistence.annotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
    spec:
      accessModes:
      - {{ .Values.persistence.accessMode }}
      {{- if .Values.persistence.storageClass }}
      storageClassName: {{ .Values.persistence.storageClass }}
      {{- end }}
      resources:
        requests:
          storage: {{ .Values.persistence.size }}
  {{- end }}
```

---

## templates/service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ollama.fullname" . }}
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
  {{- with .Values.service.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  type: {{ .Values.service.type }}
  ports:
  - port: {{ .Values.service.port }}
    targetPort: {{ .Values.service.targetPort }}
    protocol: TCP
    name: http
  {{- if .Values.metrics.enabled }}
  - port: {{ .Values.metrics.port }}
    targetPort: {{ .Values.metrics.port }}
    protocol: TCP
    name: metrics
  {{- end }}
  selector:
    {{- include "ollama.selectorLabels" . | nindent 4 }}

---
# Headless service for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ollama.fullname" . }}-headless
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
spec:
  clusterIP: None
  ports:
  - port: {{ .Values.service.port }}
    targetPort: {{ .Values.service.targetPort }}
    protocol: TCP
    name: http
  selector:
    {{- include "ollama.selectorLabels" . | nindent 4 }}
```

---

## templates/hpa.yaml

```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "ollama.fullname" . }}
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: {{ include "ollama.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  {{- if .Values.autoscaling.metrics.cpu.enabled }}
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.metrics.cpu.targetAverageUtilization }}
  {{- end }}
  {{- if .Values.autoscaling.metrics.memory.enabled }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.metrics.memory.targetAverageUtilization }}
  {{- end }}
  {{- if .Values.autoscaling.metrics.queueLength.enabled }}
  - type: Pods
    pods:
      metric:
        name: {{ .Values.autoscaling.metrics.queueLength.metricName }}
      target:
        type: AverageValue
        averageValue: {{ .Values.autoscaling.metrics.queueLength.targetAverageValue | quote }}
  {{- end }}
  {{- if .Values.autoscaling.metrics.responseTime.enabled }}
  - type: Pods
    pods:
      metric:
        name: {{ .Values.autoscaling.metrics.responseTime.metricName }}
      target:
        type: AverageValue
        averageValue: {{ .Values.autoscaling.metrics.responseTime.targetAverageValue | quote }}
  {{- end }}
  {{- if .Values.autoscaling.behavior }}
  behavior:
    {{- toYaml .Values.autoscaling.behavior | nindent 4 }}
  {{- end }}
{{- end }}
```

---

## templates/servicemonitor.yaml

```yaml
{{- if and .Values.metrics.enabled .Values.metrics.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "ollama.fullname" . }}
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
    {{- with .Values.metrics.serviceMonitor.additionalLabels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
spec:
  selector:
    matchLabels:
      {{- include "ollama.selectorLabels" . | nindent 6 }}
  endpoints:
  - port: metrics
    interval: {{ .Values.metrics.serviceMonitor.interval }}
    scrapeTimeout: {{ .Values.metrics.serviceMonitor.scrapeTimeout }}
    path: {{ .Values.metrics.path }}
{{- end }}
```

---

## templates/pdb.yaml

```yaml
{{- if .Values.podDisruptionBudget.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "ollama.fullname" . }}
  labels:
    {{- include "ollama.labels" . | nindent 4 }}
spec:
  minAvailable: {{ .Values.podDisruptionBudget.minAvailable }}
  selector:
    matchLabels:
      {{- include "ollama.selectorLabels" . | nindent 6 }}
{{- end }}
```

---

## templates/NOTES.txt

```
1. Get the application URL by running these commands:
{{- if .Values.ingress.enabled }}
{{- range $host := .Values.ingress.hosts }}
  {{- range .paths }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ $host.host }}{{ .path }}
  {{- end }}
{{- end }}
{{- else if contains "NodePort" .Values.service.type }}
  export NODE_PORT=$(kubectl get --namespace {{ .Release.Namespace }} -o jsonpath="{.spec.ports[0].nodePort}" services {{ include "ollama.fullname" . }})
  export NODE_IP=$(kubectl get nodes --namespace {{ .Release.Namespace }} -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
{{- else if contains "LoadBalancer" .Values.service.type }}
     NOTE: It may take a few minutes for the LoadBalancer IP to be available.
           You can watch the status of by running 'kubectl get --namespace {{ .Release.Namespace }} svc -w {{ include "ollama.fullname" . }}'
  export SERVICE_IP=$(kubectl get svc --namespace {{ .Release.Namespace }} {{ include "ollama.fullname" . }} --template "{{"{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}"}}")
  echo http://$SERVICE_IP:{{ .Values.service.port }}
{{- else if contains "ClusterIP" .Values.service.type }}
  export POD_NAME=$(kubectl get pods --namespace {{ .Release.Namespace }} -l "{{ include "ollama.selectorLabels" . }}" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace {{ .Release.Namespace }} $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace {{ .Release.Namespace }} port-forward $POD_NAME 8080:$CONTAINER_PORT
{{- end }}

2. Monitor the deployment:
   kubectl get statefulsets,pods,svc,hpa -l app.kubernetes.io/name={{ include "ollama.name" . }}

3. Check auto-scaling status:
   kubectl describe hpa {{ include "ollama.fullname" . }}

4. View logs:
   kubectl logs -f statefulset/{{ include "ollama.fullname" . }}

5. Test the API:
   curl http://localhost:{{ .Values.service.port }}/api/tags

{{- if .Values.autoscaling.enabled }}

Auto-scaling is ENABLED with:
- Min replicas: {{ .Values.autoscaling.minReplicas }}
- Max replicas: {{ .Values.autoscaling.maxReplicas }}
- Scaling triggers:
{{- if .Values.autoscaling.metrics.cpu.enabled }}
  ✓ CPU utilization > {{ .Values.autoscaling.metrics.cpu.targetAverageUtilization }}%
{{- end }}
{{- if .Values.autoscaling.metrics.memory.enabled }}
  ✓ Memory utilization > {{ .Values.autoscaling.metrics.memory.targetAverageUtilization }}%
{{- end }}
{{- if .Values.autoscaling.metrics.queueLength.enabled }}
  ✓ Queue length > {{ .Values.autoscaling.metrics.queueLength.targetAverageValue }}
{{- end }}
{{- end }}

{{- if .Values.ollama.models.preload }}

Pre-loaded models:
{{- range .Values.ollama.models.preload }}
  - {{ . }}
{{- end }}
{{- end }}
```

---

## Installation Commands

```bash
# Create namespace
kubectl create namespace ollama

# Add required dependencies (if using Prometheus for custom metrics)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus (optional, for custom metrics)
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace \
  --set server.persistentVolume.enabled=false

# Install custom metrics adapter (for queue length scaling)
kubectl apply -f https://github.com/kubernetes-sigs/prometheus-adapter/releases/latest/download/prometheus-adapter.yaml

# Install Ollama
helm install ollama ./ollama-chart \
  --namespace ollama \
  --create-namespace

# Or with custom values
helm install ollama ./ollama-chart \
  --namespace ollama \
  --create-namespace \
  --values custom-values.
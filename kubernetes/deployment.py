def generate_deployment(service):

    name = service["service"]

    runtime = (
        service["analysis"]
        ["runtime"]
    )

    port = runtime.get(
        "port",
        80
    )

    return f"""
apiVersion: apps/v1

kind: Deployment

metadata:
  name: {name}

spec:

  replicas: 2

  strategy:
    type: RollingUpdate

  selector:
    matchLabels:
      app: {name}

  template:

    metadata:
      labels:
        app: {name}

    spec:

      restartPolicy: Always

      containers:

        - name: {name}

          image: REPLACE_IMAGE

          imagePullPolicy: Always

          ports:
            - containerPort: {port}

          resources:

            requests:
              cpu: "100m"
              memory: "128Mi"

            limits:
              cpu: "500m"
              memory: "512Mi"

          livenessProbe:

            httpGet:
              path: /
              port: {port}

            initialDelaySeconds: 15
            periodSeconds: 20

          readinessProbe:

            httpGet:
              path: /
              port: {port}

            initialDelaySeconds: 5
            periodSeconds: 10

          startupProbe:

            httpGet:
              path: /
              port: {port}

            failureThreshold: 30
            periodSeconds: 10
"""
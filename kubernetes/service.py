def generate_service(service):

    name = service["service"]

    port = (
        service["analysis"]
        ["runtime"]
        .get("port", 80)
    )

    return f"""
apiVersion: v1

kind: Service

metadata:
  name: {name}

spec:

  selector:
    app: {name}

  ports:
    - port: 80
      targetPort: {port}

  type: ClusterIP
"""
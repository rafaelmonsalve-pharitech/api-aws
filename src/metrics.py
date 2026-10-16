"""
Metrics Emitter Module

Emisión de métricas custom a CloudWatch.
Requirements: 12.2, 12.3, 12.4, 12.5, 12.20
"""

from datetime import datetime
from typing import Optional


class MetricsEmitter:
    """Emisor de métricas custom a CloudWatch."""
    
    NAMESPACE = "Seven/ArkeoFleet"
    
    def __init__(self, cloudwatch_client):
        """
        Inicializa el emisor con cliente CloudWatch.
        
        Args:
            cloudwatch_client: boto3 CloudWatch client
        """
        self.client = cloudwatch_client
        self.batch = []
    
    def record_request(self, endpoint: str):
        """Registra petición a endpoint."""
        self._add_metric('RequestCount', 1, 'Count', {'Endpoint': endpoint})
    
    def record_error(self, endpoint: str, error_type: str):
        """Registra error."""
        self._add_metric('ErrorCount', 1, 'Count', {
            'Endpoint': endpoint,
            'ErrorType': error_type
        })
    
    def record_response_time(self, endpoint: str, milliseconds: float):
        """Registra tiempo de respuesta."""
        self._add_metric('ResponseTime', milliseconds, 'Milliseconds', {
            'Endpoint': endpoint
        })
    
    def record_db_connection_time(self, milliseconds: float):
        """Registra tiempo de conexión a DB."""
        self._add_metric('DatabaseConnectionTime', milliseconds, 'Milliseconds', {})
    
    def _add_metric(self, name: str, value: float, unit: str, dimensions: dict):
        """Agrega métrica al batch."""
        metric = {
            'MetricName': name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        }
        self.batch.append(metric)
    
    def flush(self):
        """Envía batch de métricas a CloudWatch."""
        if not self.batch:
            return
        
        try:
            self.client.put_metric_data(
                Namespace=self.NAMESPACE,
                MetricData=self.batch
            )
            self.batch = []
        except Exception as e:
            print(f"Error flushing metrics: {e}")

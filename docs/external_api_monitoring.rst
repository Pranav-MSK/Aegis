.. _external_api_monitoring:

External API Monitoring
=======================

This section explains how to monitor external API endpoints by counting the number of requests, measuring request duration, and tracking various other metrics.

Counting Requests
-----------------
To count the number of requests made to specific API endpoints, you can use the `Counter` class from the `prometheus_client` library. The following example demonstrates how to count requests to the homepage:

.. code:: python

    from prometheus_client import Counter

    homepage_request_count = Counter('homepage_request_count', 'Count of requests to homepage')

    @api.route('/')
    def homepage():
        homepage_request_count.inc()
        return 'Hello, World!'


Measuring Request Duration
--------------------------
To measure the time duration of requests to specific API endpoints, you can use the `Summary` class from the `prometheus_client` library. The following example demonstrates how to measure the request duration for the homepage:

.. code-block:: python

    from prometheus_client import Summary

    homepage_request_duration = Summary('homepage_request_duration_seconds', 'Time spent processing request to homepage')

    @api.route('/')
    @homepage_request_duration.time()
    def homepage():
        return 'Hello, World!'

Combining Request Counting and Duration Measurement
---------------------------------------------------
You can combine both request counting and duration measurement for a comprehensive monitoring solution. The following example demonstrates how to count requests and measure their duration for the homepage:

.. code-block:: python

    from prometheus_client import Counter, Summary

    homepage_request_count = Counter('homepage_request_count', 'Count of requests to homepage')
    homepage_request_duration = Summary('homepage_request_duration_seconds', 'Time spent processing request to homepage')

    @api.route('/')
    @homepage_request_duration.time()
    def homepage():
        homepage_request_count.inc()
        return 'Hello, World!'

Additional Metrics
------------------
In addition to counting requests and measuring request duration, you can monitor other important metrics such as response size, error count, active requests, request latency, and random gauge values.

Size of Responses in Bytes
~~~~~~~~~~~~~~~~~~~~~~~~~~
To track the size of responses in bytes, you can use the `Summary` class. The following example demonstrates how to measure the size of responses:

.. code-block:: python

    from prometheus_client import Summary

    response_size = Summary('response_size_bytes', 'Size of responses in bytes')

    @api.route('/')
    def homepage():
        response = 'Hello, World!'
        response_size.observe(len(response))
        return response

Total Number of Errors
~~~~~~~~~~~~~~~~~~~~~~
To count the total number of errors, you can use the `Counter` class. The following example demonstrates how to count errors:

.. code-block:: python

    from prometheus_client import Counter

    error_count = Counter('error_count', 'Total number of errors')

    @api.route('/error')
    def error_endpoint():
        try:
            # Simulate an error
            raise ValueError('An error occurred')
        except ValueError:
            error_count.inc()
            return 'Error', 500

Active Requests Gauge
~~~~~~~~~~~~~~~~~~~~~
To track the number of active requests, you can use the `Gauge` class. The following example demonstrates how to monitor active requests:

.. code-block:: python

    from prometheus_client import Gauge

    active_requests = Gauge('active_requests', 'Number of active requests')

    @api.before_request
    def before_request():
        active_requests.inc()

    @api.after_request
    def after_request(response):
        active_requests.dec()
        return response

Histogram for Request Latency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To measure request latency in seconds, you can use the `Histogram` class. The following example demonstrates how to track request latency:

.. code-block:: python

    from prometheus_client import Histogram

    request_latency = Histogram('request_latency_seconds', 'Request latency in seconds')

    @api.route('/')
    @request_latency.time()
    def homepage():
        return 'Hello, World!'

Random Gauge Value
~~~~~~~~~~~~~~~~~~
To track a random gauge value, you can use the `Gauge` class. The following example demonstrates how to set a random gauge value:

.. code-block:: python
    
    from prometheus_client import Gauge
    import random

    random_gauge = Gauge('random_gauge', 'A random gauge value')

    @api.route('/random')
    def random_value():
        value = random.random()
        random_gauge.set(value)
        return f'Random value: {value}'

Expose Metrics to SystemGuard/Prometheus
----------------------------------------

To expose the metrics to SystemGuard or Prometheus, you need to start a http server that serves the metrics. The following example demonstrates how to expose the metrics on port 8080:

.. code-block:: python

    from prometheus_client import start_http_server

    start_http_server(8080)

After running the above code, you can access the metrics at `http://localhost:8080/metrics`.

.. # now configure the systemgaurd to see the metrics : TODO
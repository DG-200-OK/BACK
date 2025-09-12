from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json
import logging
import time

import os # Import os module

# Define log file path
log_file_path = os.path.join(os.path.dirname(__file__), 'app.log') # Log file in the same directory as middlewares.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path), # Log to file
        logging.StreamHandler() # Also log to console
    ]
)
logger = logging.getLogger(__name__)

async def response_wrapper_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # OpenAPI docs paths
    if request.url.path in ["/api/docs", "/api/redoc", "/openapi.json"]:
        return response

    if response.headers.get("content-type") == "application/json":
        response_body = [chunk async for chunk in response.body_iterator][0].decode()
        try:
            data = json.loads(response_body)
            # Check if the response is already in the desired format
            if isinstance(data, dict) and 'success' in data and 'responseData' in data:
                return Response(content=response_body.encode(), status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

            return JSONResponse(
                status_code=response.status_code,
                content={
                    "success": True,
                    "responseData": data,
                    "statusCode": response.status_code,
                    "message": "요청에 성공하였습니다.",
                },
            )
        except json.JSONDecodeError:
            # Not a JSON response, pass through
            pass
    return response

async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    
    # Read request body
    try:
        body = await request.body()
        if body:
            logger.info(f"Request Body: {body.decode()}")
    except Exception as e:
        logger.error(f"Error reading request body: {e}")

    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response Status: {response.status_code}")
    logger.info(f"Response Headers: {response.headers}")
    
    # Read response body
    try:
        # Ensure the response body can be read again if needed by other middlewares
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        if response_body:
            logger.info(f"Response Body: {response_body.decode()}")
        
        # Recreate the response with the read body
        return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    except Exception as e:
        logger.error(f"Error reading response body: {e}")
        return response # Return original response if body reading fails

package maxdev.env.controller;

import maxdev.env.exception.ResourceNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import maxdev.env.dto.ErrorResponse;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.context.request.WebRequest;
import java.time.Instant;

@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgumentException(IllegalArgumentException e, WebRequest req){
        return build(HttpStatus.BAD_REQUEST, "Please make sure you sent a valid field", e.getMessage(), req);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleRuntimeException(ResourceNotFoundException e, WebRequest req){
        return build(HttpStatus.NOT_FOUND, "Resource was not found!", e.getMessage(), req);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception e, WebRequest req) {
        return build(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error!", e.getMessage(), req);
    }

    private ResponseEntity<ErrorResponse> build(HttpStatus status, String message, String error, WebRequest req){
        ErrorResponse body = new ErrorResponse(
                Instant.now().toString(),
                status.value(),
                error,
                message,
                req.getDescription(false).replace("uri=","")
        );

        return ResponseEntity.status(status.value()).body(body);
    }
}


package hird.service.collector;

import java.util.Map;
import java.util.HashMap;
import org.springframework.web.bind.MethodArgumentNotValidException;

public final class ValidationErrorCollector {

    private ValidationErrorCollector() {}

    public static Map<String, String> collect(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();

        ex
          .getBindingResult()
          .getFieldErrors()
          .forEach(error ->
                  errors.put(error.getField(), error.getDefaultMessage())
          );

        return errors;
    }
}


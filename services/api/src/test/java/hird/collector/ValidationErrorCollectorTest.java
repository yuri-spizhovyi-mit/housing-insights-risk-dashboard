package hird.collector;

import hird.service.collector.ValidationErrorCollector;
import org.junit.jupiter.api.Test;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class ValidationErrorCollectorTest {
    @Test
    public void collectsFieldErrorsIntoMap() {
        BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(new Object(), "request");
        bindingResult.addError(new FieldError("request", "city", "must not be blank"));
        bindingResult.addError(new FieldError("request", "horizon", "must be positive"));

        MethodArgumentNotValidException ex = new MethodArgumentNotValidException(null, bindingResult);

        Map<String, String> errors = ValidationErrorCollector.collect(ex);

        assertEquals(2, errors.size());
        assertEquals("must not be blank", errors.get("city"));
        assertEquals("must be positive", errors.get("horizon"));
    }
}
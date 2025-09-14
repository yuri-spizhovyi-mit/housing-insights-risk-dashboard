package maxdev.env.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    @GetMapping("/health")
    public ResponseEntity<?> getVerificationMessage(){
        return ResponseEntity.ok("OK");
    }

    @GetMapping("/info")
    public ResponseEntity<?> getInfo(){
        return ResponseEntity.ok("Welcome to the Housing Price Predicting App!");
    }    
}

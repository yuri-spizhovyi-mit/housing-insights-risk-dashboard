package hird.controller;

import hird.dto.SentimentResponse;
import hird.service.SentimentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(path = "/api/v1/sentiment")
public class SentimentController {
    private final SentimentService service;

    public SentimentController(SentimentService service){
        this.service = service;
    }

    @GetMapping
    public ResponseEntity<SentimentResponse> getSentiments(@RequestParam String city){
        SentimentResponse sentiment = service.retrieveSentiment(city);
        return ResponseEntity.ok(sentiment);
    }
}

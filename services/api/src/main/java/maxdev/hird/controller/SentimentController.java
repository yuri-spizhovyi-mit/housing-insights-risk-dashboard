package maxdev.hird.controller;


import maxdev.hird.dto.SentimentResponse;
import maxdev.hird.service.SentimentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/sentiment")
public class SentimentController {
    private final SentimentService sentimentService;

    public SentimentController(SentimentService sentimentService){
        this.sentimentService = sentimentService;
    }

    @GetMapping
    public ResponseEntity<SentimentResponse> getSentiments(@RequestParam String city){
        SentimentResponse sentiment = sentimentService.retrieveSentiment(city);
        return ResponseEntity.ok(sentiment);
    }
}

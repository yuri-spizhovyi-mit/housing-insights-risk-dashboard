package hird.collector;

import hird.dto.SentimentItemResponse;
import hird.model.SentimentEntry;
import hird.service.collector.SentimentItemCollector;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class SentimentItemCollectorTest {
    @Test
    void mapsEntitiesToResponses() {
        SentimentEntry sentiment = new SentimentEntry(
                1,
                "Kelowna",
                "positive",
                "Market strong",
                LocalDate.of(2025, 1, 1),
                "http://example.com/1"
        );

        List<SentimentItemResponse> result =
                SentimentItemCollector.collect(List.of(sentiment));

        assertEquals(1, result.size());

        SentimentItemResponse itemResponse = result.get(0);

        assertEquals("2025-01-01", itemResponse.date());
        assertEquals("Market strong", itemResponse.headline());
        assertEquals("positive", itemResponse.sentiment());
        assertEquals("http://example.com/1", itemResponse.url());
    }

}

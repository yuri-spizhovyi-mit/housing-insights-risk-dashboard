package hird.service;

import hird.dto.SentimentItemResponse;
import hird.dto.SentimentResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.model.SentimentEntry;
import hird.repository.SentimentRepository;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

public class SentimentServiceTest {

    @Test
    void returnsSentimentWhenDataExists() {
        SentimentRepository repo = mock(SentimentRepository.class);

        SentimentEntry row1 = new SentimentEntry(
                1,
                "Kelowna",
                "positive",
                "Market strong",
                LocalDate.of(2025, 1, 1),
                "http://example.com/1"
        );

        when(repo.findTop3ByCityOrderByDateDescIdDesc("Kelowna"))
                .thenReturn(List.of(row1));

        SentimentService service = new SentimentService(repo);

        SentimentResponse response = service.retrieveSentiment("Kelowna");

        assertEquals("Kelowna", response.city());
        assertEquals(1, response.items().size());

        SentimentItemResponse item = response.items().get(0);
        assertEquals("2025-01-01", item.date());
        assertEquals("Market strong", item.headline());
        assertEquals("positive", item.sentiment());
        assertEquals("http://example.com/1", item.url());
    }

    @Test
    void throwsNotFoundWhenNoSentiment() {
        SentimentRepository repo = mock(SentimentRepository.class);

        when(repo.findTop3ByCityOrderByDateDescIdDesc("Kelowna"))
                .thenReturn(List.of());

        SentimentService service = new SentimentService(repo);

        assertThrows(ResourceNotFoundException.class,
                () -> service.retrieveSentiment("Kelowna"));
    }
}

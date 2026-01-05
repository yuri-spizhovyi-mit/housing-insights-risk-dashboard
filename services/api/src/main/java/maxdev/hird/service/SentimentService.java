package maxdev.hird.service;

import maxdev.hird.domain.exceptions.ResourceNotFoundException;
import maxdev.hird.dto.SentimentItemResponse;
import maxdev.hird.dto.SentimentResponse;
import maxdev.hird.model.SentimentEntry;
import maxdev.hird.repository.SentimentRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SentimentService {

    private final SentimentRepository sentimentRepository;

    public SentimentService(SentimentRepository sentimentRepository) {
        this.sentimentRepository = sentimentRepository;
    }


    @Cacheable(
            value = "SENTIMENT_CACHE",
            key = "#city.toLowerCase()"
    )
    public SentimentResponse retrieveSentiment(String city) {
        List<SentimentEntry> rows =
                sentimentRepository.findLatest3ByCity(city, PageRequest.of(0, 3));

        if (rows.isEmpty()) {
            throw new ResourceNotFoundException("No sentiment data for " + city);
        }

        return new SentimentResponse(city, toItems(rows));
    }

    private List<SentimentItemResponse> toItems(List<SentimentEntry> rows) {
        return rows.stream()
                .map(this::toItem)
                .toList();
    }

    private SentimentItemResponse toItem(SentimentEntry row) {
        return new SentimentItemResponse(
                row.getDate().toString(),
                row.getHeadline(),
                row.getSentiment(),
                row.getUrl()
        );
    }
}

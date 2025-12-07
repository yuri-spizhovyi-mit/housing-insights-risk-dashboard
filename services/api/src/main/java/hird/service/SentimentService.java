package hird.service;

import hird.dto.SentimentItemResponse;
import hird.dto.SentimentResponse;
import hird.exceptions.ResourceNotFoundException;
import hird.model.SentimentEntry;
import hird.repository.SentimentRepository;
import hird.service.collector.SentimentItemCollector;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SentimentService {
    private final SentimentRepository repository;

    public SentimentService(SentimentRepository repository){
        this.repository = repository;
    }

    public SentimentResponse retrieveSentiment(String city) {
        List<SentimentEntry> rows =
                repository.findTop3ByCityOrderByDateDescIdDesc(city);

        if (rows.isEmpty())
            throw new ResourceNotFoundException("No sentiment data for " + city);

        List<SentimentItemResponse> items = SentimentItemCollector.collect(rows);
        return new SentimentResponse(city, items);
    }
}

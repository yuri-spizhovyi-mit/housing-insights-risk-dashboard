package hird.repository;

import java.util.List;
import java.util.UUID;
import hird.model.SentimentEntry;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SentimentRepository extends JpaRepository<SentimentEntry, UUID> {
    List<SentimentEntry> findTop3ByCityOrderByDateDescIdDesc(String city);
}

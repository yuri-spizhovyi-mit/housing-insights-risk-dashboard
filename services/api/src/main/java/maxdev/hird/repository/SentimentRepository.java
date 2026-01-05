package maxdev.hird.repository;

import maxdev.hird.model.SentimentEntry;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import org.springframework.data.domain.Pageable;
import java.util.List;

public interface SentimentRepository extends JpaRepository<SentimentEntry, Integer> {
    @Query("""
    SELECT s
    FROM SentimentEntry s
    WHERE LOWER(s.city) = LOWER(:city)
    ORDER BY s.date DESC
    """)
    List<SentimentEntry> findLatest3ByCity(
            @Param("city") String city,
            Pageable pageable
    );

}

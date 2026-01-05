package maxdev.hird.repository;


import maxdev.hird.dto.ForecastRequest;
import maxdev.hird.model.ModelPrediction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ModelPredictionRepository extends JpaRepository<ModelPrediction, UUID> {
    @Query("""
    SELECT mp
    FROM ModelPrediction mp
    WHERE LOWER(mp.city) = LOWER(:city)
        AND LOWER(mp.target) = LOWER(:target)
        AND LOWER(mp.modelName) = LOWER(:modelName)
        AND mp.horizonMonths between 1 and :months
    ORDER BY mp.predictDate ASC
    """)

    List<ModelPrediction> findForecastSeries(
            @Param("city") String city,
            @Param("target") String target,
            @Param("modelName") String model,
            @Param("months") int months
    );


    default List<ModelPrediction> findForecastSeries(ForecastRequest req, int months) {
        return findForecastSeries(req.city(), req.target(), req.modelName(), months);
    }

    @Query("""
    SELECT DISTINCT mp.city
    FROM ModelPrediction mp
    WHERE mp.city IS NOT NULL
    ORDER BY mp.city ASC
    """)
    List<String> findDistinctCities();

    List<ModelPrediction> findByCityIgnoreCaseAndTargetIgnoreCaseOrderByPredictDateAsc(String city, String target);
}

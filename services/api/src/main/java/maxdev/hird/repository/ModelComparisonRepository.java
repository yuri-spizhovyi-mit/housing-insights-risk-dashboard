package maxdev.hird.repository;

import maxdev.hird.model.ModelComparison;
import maxdev.hird.model.ModelComparisonId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ModelComparisonRepository extends JpaRepository<ModelComparison, ModelComparisonId> {
    @Query("""
        select mc
        from ModelComparison mc
        where lower(mc.id.city) = lower(:city)
          and lower(mc.id.target) = lower(:target)
        order by mc.id.horizonMonths asc, mc.id.modelName asc
    """)
    List<ModelComparison> findForComparison(@Param("city") String city,
                                            @Param("target") String target);
}

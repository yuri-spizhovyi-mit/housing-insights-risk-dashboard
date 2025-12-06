package hird.repository;

import hird.model.ModelPrediction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ModelPredictionRepository
        extends JpaRepository<ModelPrediction, UUID>,
        JpaSpecificationExecutor<ModelPrediction> {
}

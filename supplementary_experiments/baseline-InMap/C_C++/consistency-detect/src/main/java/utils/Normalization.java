package utils;

import java.util.AbstractMap;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class Normalization {

    /**
     * Normalize module-class scores to 0to1.
     * @param moduleToClasses Mapping from modules to classes and scores
     * @return Normalized mapping from modules to classes and scores
     */
    public static Map<String, List<Map.Entry<String, Double>>> normalizeScores(
            Map<String, List<Map.Entry<String, Double>>> moduleToClasses) {

        Map<String, List<Map.Entry<String, Double>>> normalizedModuleToClasses = new HashMap<>();

        for (String moduleName : moduleToClasses.keySet()) {
            List<Map.Entry<String, Double>> classScores = moduleToClasses.get(moduleName);

            // Get the maximum and minimum values in each module
            double maxScore = classScores.stream().mapToDouble(Map.Entry::getValue).max().orElse(0.0);
            double minScore = classScores.stream().mapToDouble(Map.Entry::getValue).min().orElse(0.0);
            double range = maxScore - minScore;

            // Create a new list to store the normalized scores
            List<Map.Entry<String, Double>> normalizedScores = new ArrayList<>();
            if (range > 0) { // Prevent division by zero
                for (Map.Entry<String, Double> entry : classScores) {
                    double normalizedScore = (entry.getValue() - minScore) / range;
                    normalizedScores.add(new AbstractMap.SimpleEntry<>(entry.getKey(), normalizedScore));
                }
            } else { // If all scores are the same, assign them evenly
                for (Map.Entry<String, Double> entry : classScores) {
                    normalizedScores.add(new AbstractMap.SimpleEntry<>(entry.getKey(), 1.0)); // Set all to 1,because there is no range difference
                }
            }

            // Sort the normalized scores with higher scores first
            normalizedScores.sort((a, b) -> Double.compare(b.getValue(), a.getValue()));

            // Put the normalized and sorted list into the new mapping
            normalizedModuleToClasses.put(moduleName, normalizedScores);
        }

        return normalizedModuleToClasses;
    }

    // Other methods can be added
}


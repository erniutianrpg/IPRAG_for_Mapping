package utils;
import smile.clustering.DBSCAN;
import smile.math.distance.EuclideanDistance;
import java.util.*;

public class DBSCANFilter {

    /**
     * Filter classes in the module and remove classes belonging to the lowest-scoring cluster
     * @param moduleToClasses Mapping from modules to classes and scores
     * @param eps DBSCANneighborhood radius of the DBSCAN algorithm
     * @param minPts DBSCANminimum number of points for the DBSCAN algorithm
     * @return Return the filtered module-to-class mapping
     */
    public static Map<String, String> filterLowScoringClusters(
            Map<String, List<Map.Entry<String, Double>>> moduleToClasses, double eps, int minPts) {

        Map<String, String> classToModuleMap = new HashMap<>();
        Map<String, List<String>> filteredModuleToClasses = new HashMap<>();

        for (Map.Entry<String, List<Map.Entry<String, Double>>> entry : moduleToClasses.entrySet()) {
            String moduleName = entry.getKey();
            List<Map.Entry<String, Double>> classesAndScores = entry.getValue();
            classesAndScores.sort(Map.Entry.comparingByValue());

            // Extract score data
            double[][] scores = new double[classesAndScores.size()][1];
            for (int i = 0; i < classesAndScores.size(); i++) {
                scores[i][0] = classesAndScores.get(i).getValue();
            }

            // Run DBSCAN
            DBSCAN<double[]> dbscan = DBSCAN.fit(scores, minPts, eps);

            // Get clustering results
            int[] labels = dbscan.y;

            // Compute the average score of each cluster
            Map<Integer, Double> clusterAverages = new HashMap<>();
            Map<Integer, Integer> clusterSizes = new HashMap<>();
            for (int i = 0; i < labels.length; i++) {
                int label = labels[i];
                if (label != -1) { // Ignore noise data
                    clusterAverages.put(label, clusterAverages.getOrDefault(label, 0.0) + scores[i][0]);
                    clusterSizes.put(label, clusterSizes.getOrDefault(label, 0) + 1);
                }
            }
            clusterAverages.forEach((key, value) -> clusterAverages.put(key, value / clusterSizes.get(key)));

// Sort clusters and name them
            List<Map.Entry<Integer, Double>> sortedClusters = new ArrayList<>(clusterAverages.entrySet());
            sortedClusters.sort(Map.Entry.comparingByValue(Comparator.reverseOrder()));

            // Assign a new module name to each cluster and create the class-to-module mapping
            int rank = 1;
            for (Map.Entry<Integer, Double> cluster : sortedClusters) {
                String newModuleName = moduleName + "_(" + rank + ")";
                for (int i = 0; i < labels.length; i++) {
                    if (labels[i] == cluster.getKey()) {
                        String file= classesAndScores.get(i).getKey();
                        Double score=classesAndScores.get(i).getValue();
                        classToModuleMap.put(file, newModuleName);
                    }
                }
                rank++;
            }
        }

        return classToModuleMap;
    }
}

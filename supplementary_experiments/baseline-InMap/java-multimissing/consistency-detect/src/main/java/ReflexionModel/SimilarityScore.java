package ReflexionModel;

//import ai.onnxruntime.OrtException;
import entity.ModuleMappingResult;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.*;
import org.apache.lucene.store.FSDirectory;
import utils.DBSCANFilter;
import utils.Normalization;

import java.io.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Paths;
import java.util.*;

//import static ReflexionModel.BertSimilarity.bertCalculate;
import static java.util.stream.Collectors.toMap;

public class SimilarityScore {

    static List<String> moduleNameListField = new ArrayList<>();
    static List<String> ModuleDescriptionListField =  new ArrayList<>();

    static final String[] stopWords = { "a", "able", "about", "after", "all", "almost", "also", "am", "among", "an", "and", "are", "as", "at", "be", "because",
            "been", "but", "by", "can", "could", "dear", "did", "do", "does", "else", "ever", "for", "from", "get", "got", "had", "has",
            "have", "he", "her", "hers", "him", "his", "how", "however", "i", "if", "in", "into", "is", "it", "its", "just", "let", "like", "me",
            "more", "my", "neither", "no", "nor", "of", "off", "on", "or", "other", "our", "own", "rather", "said", "say", "says",
            "she", "should", "since", "so", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "tis", "to", "too", "twas", "us",
            "wants", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "yet", "you", "your" };

    static String Processing_file_suffix=".jvtp";
    public static ModuleMappingResult run(Map<String, String> moduleMap, String projectDir, List<String> exclusionList, String project, String method, double threshold) throws IOException, ParseException, InterruptedException {
        // Index storage location
        String indexDir = projectDir+"/index";
//        String projectDir= "E:/Architecture/InconsistencyDetect/InMap/test-systems/ArgoUML";

//"E:\\Architecture\\InconsistencyDetect\\InMap\\test-systems\\Ant\\index";
//"E:\\Architecture\\InconsistencyDetect\\reflectionMaker\\test\\index";

        PreProcessing preProcess = new PreProcessing(projectDir,Processing_file_suffix);
        preProcess.cleanSourceFiles(exclusionList);
        Map<String, String> classToModule = null;
        Map<String, String> classToModule1 =null;
        Map<String, List<String>> significantScoresModules = new HashMap<>();
        Map<String, Map<String, Double>> classToModuleScores= null;
        if (method.toLowerCase().contains("lm")) {
            classToModule = getClassToModuleBert(projectDir, Processing_file_suffix, project, moduleMap, threshold);

        }
        else if (method.toLowerCase().contains("lda")) {
            classToModule = ldaCaculate( projectDir,  Processing_file_suffix,  project, moduleMap, threshold);

        }
        else if (method.toLowerCase().contains("combination")) {
            Map<String, String> classToModule_lm = getClassToModuleBert( projectDir,  Processing_file_suffix,  project, moduleMap, 0.1);
            Map<String, String> classToModule_tfidf = getClassToModule(moduleMap, indexDir, projectDir, Processing_file_suffix, project, exclusionList, 50);
            Map<String, String> combinedClassToModule = new HashMap<>();
            for (String key : classToModule_lm.keySet()) {
                if (classToModule_tfidf.containsKey(key) && classToModule_tfidf.get(key).equals(classToModule_lm.get(key))) {
                    combinedClassToModule.put(key, classToModule_lm.get(key));
                }
            }
            // Use the merged result for subsequent operations
            classToModule = combinedClassToModule;
            classToModule1=classToModule_tfidf;
        }
        else {
            classToModuleScores= getClassToModuleScores(moduleMap, indexDir, projectDir, Processing_file_suffix, project, exclusionList, threshold);
//            classToModule = getClassToModule(moduleMap, indexDir, projectDir, Processing_file_suffix, project, exclusionList, threshold);
//            classToModule = classToModule_tfidf;
        }
        System.out.println("Mapping based on "+method+", and threshold for the mapping similarity is "+threshold);

        return new ModuleMappingResult(classToModule, classToModule1,significantScoresModules,classToModuleScores);
    }

    public static Map<String, String> getClassToModule(Map<String, String> moduleMap, String indexDir, String projectDir, String processingFileSuffix, String project, List<String> exclusionList, double threshold) throws IOException, ParseException {
        IndexFiles index = new IndexFiles();
        index.indexFiles(indexDir,projectDir,Processing_file_suffix,project);


//        InvertedIndex.run(indexDir,projectFolder,exclusionList);
        // CreateDirectoryReaderandIndexSearcher
        DirectoryReader reader = DirectoryReader.open(FSDirectory.open(Paths.get(indexDir)));
        IndexSearcher searcher = new IndexSearcher(reader);

        Map<String, Map<String, Double>> classToModuleScores = new HashMap<>();
        BigDecimal mnBoostFactor = new BigDecimal("35");
        for (Map.Entry<String, String> entry : moduleMap.entrySet()) {
//            System.out.println("ModuleName: " + entry.getKey() + " ModuleDescription: " + entry.getValue());
            String moduleSearchKeywords=wordTransform(entry.getKey(),entry.getValue(),mnBoostFactor,new BigDecimal("1"));
            BooleanQuery.Builder builder = new BooleanQuery.Builder();
            for (String moduleNameWord : moduleNameListField) {
//                // Clean keywords and create a query for each keyword
//                String cleanedKeyword = entry.getKey().replaceAll("[^\\w\\s-]", "").toLowerCase();

                // Add wildcard queries
                WildcardQuery wildcardQuery = new WildcardQuery(new Term("contents", moduleNameWord + "*"));
                Query boostedWildcardQuery = new BoostQuery(wildcardQuery, mnBoostFactor.floatValue());
                builder.add(boostedWildcardQuery, BooleanClause.Occur.SHOULD);

                // Add fuzzy queries
                FuzzyQuery fuzzyQuery = new FuzzyQuery(new Term("contents", moduleNameWord));
                Query boostedFuzzyQuery = new BoostQuery(fuzzyQuery, mnBoostFactor.floatValue());
                builder.add(boostedFuzzyQuery, BooleanClause.Occur.SHOULD);
            }
            for (String moduleDescriptionWord : ModuleDescriptionListField) {
                // Add wildcard queries
                WildcardQuery wildcardQuery = new WildcardQuery(new Term("contents", moduleDescriptionWord + "*"));
                builder.add(wildcardQuery, BooleanClause.Occur.SHOULD);

                // Add fuzzy queries
                FuzzyQuery fuzzyQuery = new FuzzyQuery(new Term("contents", moduleDescriptionWord));
                builder.add(fuzzyQuery, BooleanClause.Occur.SHOULD);
            }

            Query query = builder.build();

//Simple search
//            QueryParser parser = new QueryParser("contents", new StandardAnalyzer());
//            Query query = parser.parse(moduleSearchKeywords);
            // Execute search
            TopDocs results = searcher.search(query, reader.maxDoc()); // limit to the top 10results

//            System.out.println("Found  " + results.totalHits + " results.");
            // Traverse and output results
            for (ScoreDoc hit : results.scoreDocs) {
                Document hitDoc = searcher.doc(hit.doc);
//                System.out.println("Matched document: " + hitDoc.get("path") + ", score: " + hit.score); //contains not only tf-idf,also includes document length normalization and query boost (Query Boost)


                String className = hitDoc.get("path"); // Assume filenamefield stores the class name
                if ((className.contains("MutableCounter"))){
                    Explanation explanation = searcher.explain(query, hit.doc);
                    System.out.println(moduleNameListField.toString());
                    System.out.println(explanation.toString());
                    int flag=1;
                }
                BigDecimal documentModuleAffinityScore = new BigDecimal( hit.score );
//                BigDecimal documentModuleAffinityScore = AffinityScoreAdjuster.adjustAffinityScore(
//                        new BigDecimal(hit.score),
//                        mnBoostFactor,
//                        className,
//                        entry.getKey(),
//                        project
//                );
//
//                if (className.toLowerCase().contains(entry.getKey().toLowerCase())) {
//                    documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
//                } else {
//                    if (mnBoostFactor.compareTo(BigDecimal.valueOf(0.00)) != 0) {
//                        documentModuleAffinityScore = documentModuleAffinityScore.divide(mnBoostFactor, 20, RoundingMode.HALF_UP);
//                    } else {
//                        documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
//                    }
//                }


                classToModuleScores
                        .computeIfAbsent(className, k -> new HashMap<>())
                        .put(entry.getKey(), documentModuleAffinityScore.doubleValue());

//                System.out.println("Matched document: " + className + ", adjusted score: " + documentModuleAffinityScore);

/*
                if (className.contains(entry.getKey())){
                    // Store the score in mapin
                    classToModuleScores
                            .computeIfAbsent(className, k -> new HashMap<>())
                            .put(entry.getKey(), (double) hit.score*35);

                    System.out.println("Matched document: " + className + ", score: " + hit.score*35);
                }
                else {
                    classToModuleScores
                            .computeIfAbsent(className, k -> new HashMap<>())
                            .put(entry.getKey(), (double) hit.score);

                    System.out.println("Matched document: " + className + ", score: " + hit.score*35);
                }
*/


            }

        }
//        for (Map<String, Double> scores : classToModuleScores.values()) {
//            double norm = 0.0;
//            for (double score : scores.values()) {
//                norm += score * score;
//            }
//            norm = Math.sqrt(norm);
//
//            for (Map.Entry<String, Double> entry : scores.entrySet()) {
//                scores.put(entry.getKey(), entry.getValue() / norm);
//            }
//        }

        // Close the reader
        reader.close();
//        List<String> targetClassNames = Arrays.asList(
//                "src/main/java/teammates/ui/webapi/StudentSearchIndexingWorkerAction.jvtp",
//                "src/main/java/teammates/ui/webapi/ResetAccountRequestAction.jvtp",
//                "src/main/java/teammates/ui/webapi/GetInstructorPrivilegeAction.jvtp",
//                "src/main/java/teammates/ui/webapi/DeleteDataBundleAction.jvtp"
//        );
//
//// After processing all modules and documents, output the results for all target classes
//        for (String targetClassName : targetClassNames) {
//            if (classToModuleScores.containsKey(targetClassName)) {
//                System.out.println("Class: " + targetClassName);
//                Map<String, Double> moduleScores = classToModuleScores.get(targetClassName);
//                for (Map.Entry<String, Double> scoreEntry : moduleScores.entrySet()) {
//                    System.out.println("    Module: " + scoreEntry.getKey() + ", Score: " + scoreEntry.getValue());
//                }
//            }
//        }

// Call the new function to filter the top 50%class
//        Map<String, String> topNclass2module = filterTopNPercentClassesByModule(classToModuleScores,threshold);

        Map<String, String> classToModule_tfidf = new HashMap<>();
        Map<String, List<String>> significantScoresModules = new HashMap<>(); // newMap

        int mismatch_count=0;
        for (Map.Entry<String, Map<String, Double>> entry1 : classToModuleScores.entrySet()) {
            //String className = entry1.getKey();
            String className = entry1.getKey();
            if (className.contains("ContextFactory")) {
                int flag=1;
            }
            Map<String, Double> moduleScores = entry1.getValue();
//            System.out.println(moduleScores);

            // Sort the scores
            List<Map.Entry<String, Double>> sortedEntries = new ArrayList<>(moduleScores.entrySet());
            sortedEntries.sort(Map.Entry.comparingByValue(Comparator.reverseOrder()));

            // Get the highest-scoring module
            Map.Entry<String, Double> maxEntry = sortedEntries.get(0);
            // Check whether the highest score is greater than 20
            if (maxEntry.getValue() > threshold) {
                classToModule_tfidf.put(className, maxEntry.getKey());
            }
            else{
                mismatch_count+=1;
            }
//            classToModule.put(className, maxEntry.getKey());
//            System.out.println("class " + className + " highest-scoring module: " + maxEntry.getKey() + ", score: " + maxEntry.getValue());

            // Check whether the top two scores are significantly higher than the other scores
            if (sortedEntries.size() > 3 && sortedEntries.get(0).getValue() / sortedEntries.get(3).getValue() >= 2) {
                // Check whether the second-highest score also satisfies the condition
                if (sortedEntries.get(1).getValue() / sortedEntries.get(3).getValue() >= 2) {
                    List<String> topModules = Arrays.asList(sortedEntries.get(0).getKey(), sortedEntries.get(1).getKey());
                    significantScoresModules.put(className, topModules);
                }
            }
        }


        // Based on classToModule Create moduleToClasses mapping that only contains the highest-scoring module
        Map<String, List<Map.Entry<String, Double>>> moduleToClasses = new HashMap<>();
        for (Map.Entry<String, String> classModuleEntry : classToModule_tfidf.entrySet()) {
            String className = classModuleEntry.getKey();
            String moduleName = classModuleEntry.getValue();
            Double score = classToModuleScores.get(className).get(moduleName);

            // Add the class and score as an entry to the corresponding module list
            moduleToClasses.computeIfAbsent(moduleName, k -> new ArrayList<>())
                    .add(new AbstractMap.SimpleEntry<>(className, score));

        }
        // Sort each module's list by scoredescending order
// Based on the existing  moduleToClasses (already sorted by score in descending order within each module), extract the highest-scoring class in each module that does not contain  "test" classes
        Map<String, String> filteredClassToModule = new HashMap<>();
        for (Map.Entry<String, List<Map.Entry<String, Double>>> entry : moduleToClasses.entrySet()) {
            String moduleName = entry.getKey();
            List<Map.Entry<String, Double>> classList = entry.getValue();

            // Traverse the class list sorted by score and find the first one that does not contain  "test" classes
            for (Map.Entry<String, Double> classEntry : classList) {
                String className = classEntry.getKey();
                if (!className.toLowerCase().contains("test")) {
                    filteredClassToModule.put(className, moduleName);
                    break;
                }
            }
        }

// Return a new  classToModule mapping that only contains the highest-scoring class in each module that passes the filter condition
//        return filteredClassToModule;



        return classToModule_tfidf;
    }

    public static Map<String, Map<String, Double>> getClassToModuleScores(Map<String, String> moduleMap, String indexDir, String projectDir, String processingFileSuffix, String project, List<String> exclusionList, double threshold) throws IOException, ParseException {
        IndexFiles index = new IndexFiles();
        index.indexFiles(indexDir,projectDir,Processing_file_suffix,project);


//        InvertedIndex.run(indexDir,projectFolder,exclusionList);
        // CreateDirectoryReaderandIndexSearcher
        DirectoryReader reader = DirectoryReader.open(FSDirectory.open(Paths.get(indexDir)));
        IndexSearcher searcher = new IndexSearcher(reader);

        Map<String, Map<String, Double>> classToModuleScores = new HashMap<>();
        BigDecimal mnBoostFactor = new BigDecimal("35");
        for (Map.Entry<String, String> entry : moduleMap.entrySet()) {
//            System.out.println("ModuleName: " + entry.getKey() + " ModuleDescription: " + entry.getValue());
            String moduleSearchKeywords=wordTransform(entry.getKey(),entry.getValue(),mnBoostFactor,new BigDecimal("1"));
            BooleanQuery.Builder builder = new BooleanQuery.Builder();
            for (String moduleNameWord : moduleNameListField) {
//                // Clean keywords and create a query for each keyword
//                String cleanedKeyword = entry.getKey().replaceAll("[^\\w\\s-]", "").toLowerCase();

                // Add wildcard queries
                WildcardQuery wildcardQuery = new WildcardQuery(new Term("contents", moduleNameWord + "*"));
                Query boostedWildcardQuery = new BoostQuery(wildcardQuery, mnBoostFactor.floatValue());
                builder.add(boostedWildcardQuery, BooleanClause.Occur.SHOULD);

                // Add fuzzy queries
                FuzzyQuery fuzzyQuery = new FuzzyQuery(new Term("contents", moduleNameWord));
                Query boostedFuzzyQuery = new BoostQuery(fuzzyQuery, mnBoostFactor.floatValue());
                builder.add(boostedFuzzyQuery, BooleanClause.Occur.SHOULD);
            }
            for (String moduleDescriptionWord : ModuleDescriptionListField) {
                // Add wildcard queries
                WildcardQuery wildcardQuery = new WildcardQuery(new Term("contents", moduleDescriptionWord + "*"));
                builder.add(wildcardQuery, BooleanClause.Occur.SHOULD);

                // Add fuzzy queries
                FuzzyQuery fuzzyQuery = new FuzzyQuery(new Term("contents", moduleDescriptionWord));
                builder.add(fuzzyQuery, BooleanClause.Occur.SHOULD);
            }

            Query query = builder.build();

//Simple search
//            QueryParser parser = new QueryParser("contents", new StandardAnalyzer());
//            Query query = parser.parse(moduleSearchKeywords);
            // Execute search
            TopDocs results = searcher.search(query, reader.maxDoc()); // limit to the top 10results

//            System.out.println("Found  " + results.totalHits + " results.");
            // Traverse and output results
            for (ScoreDoc hit : results.scoreDocs) {
                Document hitDoc = searcher.doc(hit.doc);
//                System.out.println("Matched document: " + hitDoc.get("path") + ", score: " + hit.score); //contains not only tf-idf,also includes document length normalization and query boost (Query Boost)


                String className = hitDoc.get("path"); // Assume filenamefield stores the class name
                if ((className.contains("MutableCounter"))){
                    Explanation explanation = searcher.explain(query, hit.doc);
                    System.out.println(moduleNameListField.toString());
                    System.out.println(explanation.toString());
                    int flag=1;
                }
                BigDecimal documentModuleAffinityScore = new BigDecimal( hit.score );
//                BigDecimal documentModuleAffinityScore = AffinityScoreAdjuster.adjustAffinityScore(
//                        new BigDecimal(hit.score),
//                        mnBoostFactor,
//                        className,
//                        entry.getKey(),
//                        project
//                );
//
//                if (className.toLowerCase().contains(entry.getKey().toLowerCase())) {
//                    documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
//                } else {
//                    if (mnBoostFactor.compareTo(BigDecimal.valueOf(0.00)) != 0) {
//                        documentModuleAffinityScore = documentModuleAffinityScore.divide(mnBoostFactor, 20, RoundingMode.HALF_UP);
//                    } else {
//                        documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
//                    }
//                }


                classToModuleScores
                        .computeIfAbsent(className, k -> new HashMap<>())
                        .put(entry.getKey(), documentModuleAffinityScore.doubleValue());

//                System.out.println("Matched document: " + className + ", adjusted score: " + documentModuleAffinityScore);

/*
                if (className.contains(entry.getKey())){
                    // Store the score in mapin
                    classToModuleScores
                            .computeIfAbsent(className, k -> new HashMap<>())
                            .put(entry.getKey(), (double) hit.score*35);

                    System.out.println("Matched document: " + className + ", score: " + hit.score*35);
                }
                else {
                    classToModuleScores
                            .computeIfAbsent(className, k -> new HashMap<>())
                            .put(entry.getKey(), (double) hit.score);

                    System.out.println("Matched document: " + className + ", score: " + hit.score*35);
                }
*/


            }

        }
//        for (Map<String, Double> scores : classToModuleScores.values()) {
//            double norm = 0.0;
//            for (double score : scores.values()) {
//                norm += score * score;
//            }
//            norm = Math.sqrt(norm);
//
//            for (Map.Entry<String, Double> entry : scores.entrySet()) {
//                scores.put(entry.getKey(), entry.getValue() / norm);
//            }
//        }

        // Close the reader
        reader.close();
//        List<String> targetClassNames = Arrays.asList(
//                "src/main/java/teammates/ui/webapi/StudentSearchIndexingWorkerAction.jvtp",
//                "src/main/java/teammates/ui/webapi/ResetAccountRequestAction.jvtp",
//                "src/main/java/teammates/ui/webapi/GetInstructorPrivilegeAction.jvtp",
//                "src/main/java/teammates/ui/webapi/DeleteDataBundleAction.jvtp"
//        );
//
//// After processing all modules and documents, output the results for all target classes
//        for (String targetClassName : targetClassNames) {
//            if (classToModuleScores.containsKey(targetClassName)) {
//                System.out.println("Class: " + targetClassName);
//                Map<String, Double> moduleScores = classToModuleScores.get(targetClassName);
//                for (Map.Entry<String, Double> scoreEntry : moduleScores.entrySet()) {
//                    System.out.println("    Module: " + scoreEntry.getKey() + ", Score: " + scoreEntry.getValue());
//                }
//            }
//        }

// Call the new function to filter the top 50%class
//        Map<String, String> topNclass2module = filterTopNPercentClassesByModule(classToModuleScores,threshold);

        Map<String, String> classToModule_tfidf = new HashMap<>();
        Map<String, List<String>> significantScoresModules = new HashMap<>(); // newMap

        int mismatch_count=0;
        for (Map.Entry<String, Map<String, Double>> entry1 : classToModuleScores.entrySet()) {
            //String className = entry1.getKey();
            String className = entry1.getKey();
            if (className.contains("ContextFactory")) {
                int flag=1;
            }
            Map<String, Double> moduleScores = entry1.getValue();
//            System.out.println(moduleScores);

            // Sort the scores
            List<Map.Entry<String, Double>> sortedEntries = new ArrayList<>(moduleScores.entrySet());
            sortedEntries.sort(Map.Entry.comparingByValue(Comparator.reverseOrder()));

            // Get the highest-scoring module
            Map.Entry<String, Double> maxEntry = sortedEntries.get(0);
            // Check whether the highest score is greater than 20
            if (maxEntry.getValue() > threshold) {
                classToModule_tfidf.put(className, maxEntry.getKey());
            }
            else{
                mismatch_count+=1;
            }
//            classToModule.put(className, maxEntry.getKey());
//            System.out.println("class " + className + " highest-scoring module: " + maxEntry.getKey() + ", score: " + maxEntry.getValue());

            // Check whether the top two scores are significantly higher than the other scores
            if (sortedEntries.size() > 3 && sortedEntries.get(0).getValue() / sortedEntries.get(3).getValue() >= 2) {
                // Check whether the second-highest score also satisfies the condition
                if (sortedEntries.get(1).getValue() / sortedEntries.get(3).getValue() >= 2) {
                    List<String> topModules = Arrays.asList(sortedEntries.get(0).getKey(), sortedEntries.get(1).getKey());
                    significantScoresModules.put(className, topModules);
                }
            }
        }


        // Based on classToModule Create moduleToClasses mapping that only contains the highest-scoring module
        Map<String, List<Map.Entry<String, Double>>> moduleToClasses = new HashMap<>();
        for (Map.Entry<String, String> classModuleEntry : classToModule_tfidf.entrySet()) {
            String className = classModuleEntry.getKey();
            String moduleName = classModuleEntry.getValue();
            Double score = classToModuleScores.get(className).get(moduleName);

            // Add the class and score as an entry to the corresponding module list
            moduleToClasses.computeIfAbsent(moduleName, k -> new ArrayList<>())
                    .add(new AbstractMap.SimpleEntry<>(className, score));

        }
        // Sort each module's list by scoredescending order
// Based on the existing  moduleToClasses (already sorted by score in descending order within each module), extract the highest-scoring class in each module that does not contain  "test" classes
        Map<String, String> filteredClassToModule = new HashMap<>();
        for (Map.Entry<String, List<Map.Entry<String, Double>>> entry : moduleToClasses.entrySet()) {
            String moduleName = entry.getKey();
            List<Map.Entry<String, Double>> classList = entry.getValue();

            // Traverse the class list sorted by score and find the first one that does not contain  "test" classes
            for (Map.Entry<String, Double> classEntry : classList) {
                String className = classEntry.getKey();
                if (!className.toLowerCase().contains("test")) {
                    filteredClassToModule.put(className, moduleName);
                    break;
                }
            }
        }

// Return a new  classToModule mapping that only contains the highest-scoring class in each module that passes the filter condition
//        return filteredClassToModule;



        return classToModuleScores;
    }

    public static Map<String, String> getClassToModuleBert(String projectDir, String processingFileSuffix, String project, Map<String, String> moduleMap, double threshold) throws IOException, InterruptedException {

        Map<String, Map<String, Double>> classToModuleScores_bert = BertSimilarityClient.bertCalculate(projectDir,Processing_file_suffix,project,moduleMap);
        Map<String, String> classToModule_bert = new HashMap<>();
        Map<String, Double> maxScores = new HashMap<>();
        List<Double> scores = new ArrayList<>();
//        Map<String, String> topNclass2module = filterTopNPercentClassesByModule(classToModuleScores_bert,threshold);
        for (Map.Entry<String, Map<String, Double>> entry1 : classToModuleScores_bert.entrySet()) {
            // Get the maximum score
            double maxScore = Collections.max(entry1.getValue().values());
            maxScores.put(entry1.getKey(), maxScore);
            scores.add(maxScore);

            String className = entry1.getKey();
            if (className.contains("QueryLogsParams")) {
                int flag = 1;
            }
            boolean skipRemaining = false; // Flag that controls whether subsequent code is skipped
            Map<String, Double> moduleScores = entry1.getValue();
//            for (String moduleName:moduleScores.keySet()){
//                if (className.toLowerCase().contains(moduleName.toLowerCase())){
//                    classToModule_bert.put(className, moduleName);
//                    skipRemaining = true; // Set the flag to skip subsequent code
//                    break;
//                }
//            }
            if (skipRemaining) {
                continue; // Skip the remaining code in the current iteration
            }

            // Sort the scores
            List<Map.Entry<String, Double>> sortedEntries = new ArrayList<>(moduleScores.entrySet());
            sortedEntries.sort(Map.Entry.comparingByValue(Comparator.reverseOrder()));

            // Get the highest-scoring module
            Map.Entry<String, Double> maxEntry = sortedEntries.get(0);
            // Check whether the highest score is greater than 0
            if (maxEntry.getValue() > threshold) {
                classToModule_bert.put(className, maxEntry.getKey());
            }
        }
        // Compute the mean and standard deviation
        double sum = 0.0;
        for (double score : scores) {
            sum += score;
        }
        double mean = sum / scores.size();

        double sumOfSquares = 0.0;
        for (double score : scores) {
            sumOfSquares += Math.pow(score - mean, 2);
        }
        double standardDeviation = Math.sqrt(sumOfSquares / scores.size());
        return classToModule_bert;
    }
    // Helper function: filter the top 50%class
// Helper function: filter the top 50% highest-scoring classes by module
    public static Map<String, String> filterTopNPercentClassesByModule(Map<String, Map<String, Double>> classToModuleScores, double threshold) {
        // Convert to a module-centered structure
        Map<String, List<Map.Entry<String, Double>>> moduleToClassScores = new HashMap<>();

        for (Map.Entry<String, Map<String, Double>> entry : classToModuleScores.entrySet()) {
            String className = entry.getKey();
            Map<String, Double> moduleScores = entry.getValue();

            // Find the highest-scoring module
            String bestModule = null;
            double maxScore = Double.NEGATIVE_INFINITY;

            for (Map.Entry<String, Double> moduleScoreEntry : moduleScores.entrySet()) {
                String moduleName = moduleScoreEntry.getKey();
                Double score = moduleScoreEntry.getValue();

                // If the current module score is higher than the recorded maximum score, update the maximum score and the corresponding module
                if (score > maxScore) {
                    maxScore = score;
                    bestModule = moduleName;
                }
            }

            // Add this class's highest-scoring module to  moduleToClassScores
            if (bestModule != null) {
                moduleToClassScores.computeIfAbsent(bestModule, k -> new ArrayList<>())
                        .add(new AbstractMap.SimpleEntry<>(className, maxScore));
            }
        }


        // Sort classes by module and keep the top 50%
        Map<String, List<String>> topClassesByModule = new HashMap<>();
        for (Map.Entry<String, List<Map.Entry<String, Double>>> entry : moduleToClassScores.entrySet()) {
            String moduleName = entry.getKey();
            List<Map.Entry<String, Double>> classScores = entry.getValue();

            // Sort by score in descending order
            classScores.sort(Map.Entry.comparingByValue(Comparator.reverseOrder()));

            // Compute the top 50%classes
            int topN = (int) Math.ceil(classScores.size() * threshold);
            List<String> topClasses = new ArrayList<>();
            for (int i = 0; i < topN; i++) {
                topClasses.add(classScores.get(i).getKey());
            }

            topClassesByModule.put(moduleName, topClasses);
        }
        // Convert topClassesByModule to classToModule and handle duplicate files
        Map<String, String> classToModule = new HashMap<>();
        Set<String> seenClasses = new HashSet<>();
        Set<String> duplicateClasses = new HashSet<>();

        for (Map.Entry<String, List<String>> entry : topClassesByModule.entrySet()) {
            String moduleName = entry.getKey();
            List<String> classList = entry.getValue();

            // Map each class to its module
            for (String className : classList) {
                if (seenClasses.contains(className)) {
                    // If this class already exists in another module, mark it as duplicate
                    duplicateClasses.add(className);
                } else {
                    seenClasses.add(className);
                    classToModule.put(className, moduleName);
                }
            }
        }

        // Remove all classes marked as duplicates
        for (String duplicateClass : duplicateClasses) {
            classToModule.remove(duplicateClass);
        }

        return classToModule;
    }

    public static Map<String, String> ldaCaculate(String projectDir, String processingFileSuffix, String project, Map<String, String> moduleMap,double threshold) throws IOException {
        ldaSimilarity similarity = new ldaSimilarity(10); // Specify the number of topics
        Map<String, String> documentContents = similarity.readCleanedFiles(projectDir, processingFileSuffix, project); // Specify the directory
        similarity.trainLdaModel(documentContents.values().toArray(new String[0]));

        Map<String, Map<String, Double>> classToModuleScores = new HashMap<>();
        // Iterating over the module map
        for (Map.Entry<String, String> moduleEntry : moduleMap.entrySet()) {
            String moduleName = moduleEntry.getKey();
            String moduleDescription = moduleEntry.getValue();

            double[] moduleDist = similarity.getEnhancedTopicDistribution(moduleName, moduleDescription, 35); // Boost factor of 5
            for (Map.Entry<String, String> entry : documentContents.entrySet()) {
                String docPath = entry.getKey();
                String docContent = entry.getValue();
                if (docPath.contains("services/tools.descartes.teastore.image/src/main/java/tools/descartes/teastore/image/storage/rules/StoreLargeImages.jvtp")){
                    if (moduleName.equals("ImageProvider")){
                        int flag=1;
                    }
                }
                double[] docDist = similarity.getTopicDistribution(docContent);
                double similarityScore = similarity.cosineSimilarity(moduleDist, docDist);
                classToModuleScores.computeIfAbsent(docPath, k -> new HashMap<>()).put(moduleName, similarityScore);
            }
        }
        // Create classToModule by selecting the module with the highest similarity score for each class
        // Create classToModule by selecting the module with the highest similarity score for each class
        Map<String, String> classToModule = new HashMap<>();
        for (Map.Entry<String, Map<String, Double>> entry : classToModuleScores.entrySet()) {
            String className = entry.getKey();
            Map<String, Double> moduleScores = entry.getValue();

            // Sort the scores in descending order
            List<Map.Entry<String, Double>> sortedEntries = new ArrayList<>(moduleScores.entrySet());
            sortedEntries.sort(Map.Entry.comparingByValue(Comparator.reverseOrder()));

            // Get the module with the highest score
            Map.Entry<String, Double> maxEntry = sortedEntries.get(0);

            // Check if the highest score exceeds the threshold
            if (maxEntry.getValue() > threshold) {
                classToModule.put(className, maxEntry.getKey());
            }
        }

        return classToModule;
    }



    private static void compare(){
        Map<String, String> fileMappings1 = new HashMap<>();
        Map<String, String> fileMappings2 = new HashMap<>();

        try (BufferedReader br1 = new BufferedReader(new FileReader("C:\\Users\\XJTU\\Desktop\\mappings1.txt"))) {
            String line;
            while ((line = br1.readLine()) != null) {
                String[] parts = line.split(" -> ");
                fileMappings1.put(parts[0], parts[1]);
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

        try (BufferedReader br2 = new BufferedReader(new FileReader("C:\\Users\\XJTU\\Desktop\\mappings2.txt"))) {
            String line;
            while ((line = br2.readLine()) != null) {
                String[] parts = line.split(" -> ");
                fileMappings2.put(parts[0], parts[1]);
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

// No. 3Step: compare mappings and output differences
        List<String> differences = new ArrayList<>();
        for (String key : fileMappings1.keySet()) {
            if (!fileMappings1.get(key).equals(fileMappings2.getOrDefault(key, ""))) {
                differences.add("Class: " + key + " - Mapping1: " + fileMappings1.get(key) + " - Mapping2: " + fileMappings2.getOrDefault(key, "Not Found"));
            }
        }

// Output differences to a file
        try (PrintWriter outDiff = new PrintWriter(new FileWriter("C:\\Users\\XJTU\\Desktop\\differences.txt"))) {
            for (String diff : differences) {
                outDiff.println(diff);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }


    }

    private static String wordTransform (String architectureModuleName, String moduleDescription, BigDecimal mnBoostFactor, BigDecimal mdBoostFactor ){
        String moduleSearchKeywords = "";

        // ADDING MODULE NAMES
        ArrayList<String> moduleNameList = new ArrayList<String>();
        architectureModuleName = architectureModuleName.replaceAll( "[^a-zA-Z0-9_\\s-]", "" );

        String moduleNameWords [] = architectureModuleName.toLowerCase().split( " " );				// for multi-word module names e.g. "architecture model"

        for( int j = 0; j < moduleNameWords.length; j++ )
        {
            String word =  moduleNameWords[ j ].replaceAll( "[^a-zA-Z0-9_\\s-]", "" );

            if( !word.equals( "" ) )
            {
                // TODO: investigate stemming further
                //stemmer.setCurrent( word.toLowerCase() );
                //stemmer.stem();  										// stem each word
                //moduleNameList.add( stemmer.getCurrent() );
                moduleNameList.add( word.toLowerCase() );
            }
        }

        if( architectureModuleName.contains( "-" ) || architectureModuleName.contains( "_" ) )			// for multi-word module names that have characters e.g. "architecture-model"
        {
            String moduleCleaned = architectureModuleName.replaceAll( "-", " " );
            moduleCleaned = moduleCleaned.replaceAll( "_", " " );
            moduleNameWords = moduleCleaned.split( " " );

            for( int j = 0; j < moduleNameWords.length; j++ )
            {
                String word = moduleNameWords[ j ].replaceAll( "[^a-zA-Z0-9_\\s-]", "" );

                if( !word.equals( "" ) )
                {
                    // TODO: investigate stemming further
                    //stemmer.setCurrent( word.toLowerCase() );
                    //stemmer.stem();  										// stem each word
                    //moduleNameList.add( stemmer.getCurrent() );
                    moduleNameList.add( word.toLowerCase() );
                }
            }
        }

        moduleSearchKeywords = moduleSearchKeywords + "(";

        for( String moduleNameWord : moduleNameList )
        {
            //moduleSearchKeywords = moduleSearchKeywords + "/\\w*" + moduleNameWord + "\\w*/";		// TODO: investigate using regex
            moduleSearchKeywords = moduleSearchKeywords + " " + moduleNameWord + "*";		// add module name words (with * wildcards and fuzzy searching) to search keywords
        }
        moduleNameListField=moduleNameList;
        moduleSearchKeywords = moduleSearchKeywords + " )^" + mnBoostFactor;

        // ADDING MODULE DESCRIPTIONS
        String moduleDescriptionWords [] = moduleDescription.split( " " );
        ArrayList<String> moduleDescriptionList = new ArrayList<String>();

        // remove characters
        for( int j = 0; j < moduleDescriptionWords.length; j++ )
        {
            String word = moduleDescriptionWords[ j ].replaceAll( "[^a-zA-Z0-9_\\s-]", "" );

            if( !word.equals( "" ) )
            {
                // TODO: investigate stemming further
                //stemmer.setCurrent( word.toLowerCase() );
                //stemmer.stem();  										// stem each word
                //moduleDescriptionList.add( stemmer.getCurrent() );
                moduleDescriptionList.add( word.toLowerCase() );
            }
        }

        // removes stop words from module descriptions
        ArrayList<String> filteredModuleDescriptionList = new ArrayList<String>();
        filteredModuleDescriptionList.addAll( moduleDescriptionList );

        for( int j = 0; j < stopWords.length; j++ )
        {
            for( String word : moduleDescriptionList )
            {
                word = word.toLowerCase();

                if( word.equals( stopWords[ j ] ) )
                {
                    filteredModuleDescriptionList.remove( word );
                }
            }
        }

        moduleSearchKeywords = moduleSearchKeywords + " (";

        ModuleDescriptionListField =filteredModuleDescriptionList;
        for( String moduleDescriptionWord : filteredModuleDescriptionList )
        {
            //moduleSearchKeywords = moduleSearchKeywords + "/\\w*" + moduleDescriptionWord + "\\w* /";		// TODO: investigate using regex
            moduleSearchKeywords = moduleSearchKeywords + " " + moduleDescriptionWord + "*";			// add module description words (with * wildcards) to search keywords
        }

        moduleSearchKeywords = moduleSearchKeywords + ")^" + mdBoostFactor;
        return moduleSearchKeywords;

    }


}

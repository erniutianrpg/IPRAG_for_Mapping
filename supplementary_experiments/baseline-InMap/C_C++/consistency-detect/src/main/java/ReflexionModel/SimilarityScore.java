package ReflexionModel;

import entity.ModuleMappingResult;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.BoostQuery;
import org.apache.lucene.search.FuzzyQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.search.WildcardQuery;
import org.apache.lucene.store.FSDirectory;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class SimilarityScore {

    static List<String> moduleNameListField = new ArrayList<>();
    static List<String> moduleDescriptionListField = new ArrayList<>();

    static final String[] stopWords = { "a", "able", "about", "after", "all", "almost", "also", "am", "among", "an", "and", "are", "as", "at", "be", "because",
            "been", "but", "by", "can", "could", "dear", "did", "do", "does", "else", "ever", "for", "from", "get", "got", "had", "has",
            "have", "he", "her", "hers", "him", "his", "how", "however", "i", "if", "in", "into", "is", "it", "its", "just", "let", "like", "me",
            "more", "my", "neither", "no", "nor", "of", "off", "on", "or", "other", "our", "own", "rather", "said", "say", "says",
            "she", "should", "since", "so", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "tis", "to", "too", "twas", "us",
            "wants", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "yet", "you", "your" };

    public static ModuleMappingResult run(Map<String, String> moduleMap, String projectDir, List<String> exclusionList, String project, String method, double threshold) throws IOException, ParseException {
        return run(moduleMap, projectDir, exclusionList, project, method, threshold, "cpp");
    }

    public static ModuleMappingResult run(Map<String, String> moduleMap, String projectDir, List<String> exclusionList, String project, String method, double threshold, String language) throws IOException, ParseException {
        if (!"tfidf".equalsIgnoreCase(method)) {
            throw new IllegalArgumentException("Only tfidf is supported in this build. Received method: " + method);
        }

        String processingFileSuffix = getProcessingFileSuffix(language);
        String indexDir = projectDir + "/index";

        PreProcessing preProcess = new PreProcessing(projectDir, processingFileSuffix, language);
        preProcess.cleanSourceFiles(exclusionList);

        Map<String, Map<String, Double>> classToModuleScores =
                getClassToModuleScores(moduleMap, indexDir, projectDir, processingFileSuffix, project);
        System.out.println("Mapping based on tfidf, and threshold for the mapping similarity is " + threshold);

        return ModuleMappingResult.forScores(classToModuleScores);
    }

    public static Map<String, Map<String, Double>> getClassToModuleScores(Map<String, String> moduleMap, String indexDir, String projectDir, String processingFileSuffix, String project) throws IOException, ParseException {
        IndexFiles index = new IndexFiles();
        index.indexFiles(indexDir, projectDir, processingFileSuffix, project);

        DirectoryReader reader = DirectoryReader.open(FSDirectory.open(Paths.get(indexDir)));
        IndexSearcher searcher = new IndexSearcher(reader);

        Map<String, Map<String, Double>> classToModuleScores = new HashMap<>();
        BigDecimal mnBoostFactor = new BigDecimal("35");
        for (Map.Entry<String, String> entry : moduleMap.entrySet()) {
            wordTransform(entry.getKey(), entry.getValue(), mnBoostFactor, new BigDecimal("1"));
            BooleanQuery.Builder builder = new BooleanQuery.Builder();

            for (String moduleNameWord : moduleNameListField) {
                WildcardQuery wildcardQuery = new WildcardQuery(new Term("contents", moduleNameWord + "*"));
                Query boostedWildcardQuery = new BoostQuery(wildcardQuery, mnBoostFactor.floatValue());
                builder.add(boostedWildcardQuery, BooleanClause.Occur.SHOULD);

                FuzzyQuery fuzzyQuery = new FuzzyQuery(new Term("contents", moduleNameWord));
                Query boostedFuzzyQuery = new BoostQuery(fuzzyQuery, mnBoostFactor.floatValue());
                builder.add(boostedFuzzyQuery, BooleanClause.Occur.SHOULD);
            }
            for (String moduleDescriptionWord : moduleDescriptionListField) {
                WildcardQuery wildcardQuery = new WildcardQuery(new Term("contents", moduleDescriptionWord + "*"));
                builder.add(wildcardQuery, BooleanClause.Occur.SHOULD);

                FuzzyQuery fuzzyQuery = new FuzzyQuery(new Term("contents", moduleDescriptionWord));
                builder.add(fuzzyQuery, BooleanClause.Occur.SHOULD);
            }

            BooleanQuery query = builder.build();
            TopDocs results = searcher.search(query, reader.maxDoc());
            for (ScoreDoc hit : results.scoreDocs) {
                Document hitDoc = searcher.doc(hit.doc);
                String className = hitDoc.get("path");
                classToModuleScores
                        .computeIfAbsent(className, k -> new HashMap<>())
                        .put(entry.getKey(), (double) hit.score);
            }
        }

        reader.close();
        return classToModuleScores;
    }

    private static String wordTransform(String architectureModuleName, String moduleDescription, BigDecimal mnBoostFactor, BigDecimal mdBoostFactor) {
        String moduleSearchKeywords = "";

        ArrayList<String> moduleNameList = new ArrayList<>();
        architectureModuleName = architectureModuleName.replaceAll("[^a-zA-Z0-9_\\s-]", "");

        String[] moduleNameWords = architectureModuleName.toLowerCase().split(" ");
        for (String moduleNameWord : moduleNameWords) {
            String word = moduleNameWord.replaceAll("[^a-zA-Z0-9_\\s-]", "");
            if (!word.equals("")) {
                moduleNameList.add(word.toLowerCase());
            }
        }

        if (architectureModuleName.contains("-") || architectureModuleName.contains("_")) {
            String moduleCleaned = architectureModuleName.replaceAll("-", " ");
            moduleCleaned = moduleCleaned.replaceAll("_", " ");
            moduleNameWords = moduleCleaned.split(" ");

            for (String moduleNameWord : moduleNameWords) {
                String word = moduleNameWord.replaceAll("[^a-zA-Z0-9_\\s-]", "");
                if (!word.equals("")) {
                    moduleNameList.add(word.toLowerCase());
                }
            }
        }

        moduleSearchKeywords = moduleSearchKeywords + "(";
        for (String moduleNameWord : moduleNameList) {
            moduleSearchKeywords = moduleSearchKeywords + " " + moduleNameWord + "*";
        }
        moduleNameListField = moduleNameList;
        moduleSearchKeywords = moduleSearchKeywords + " )^" + mnBoostFactor;

        String[] moduleDescriptionWords = moduleDescription.split(" ");
        ArrayList<String> moduleDescriptionList = new ArrayList<>();
        for (String moduleDescriptionWord : moduleDescriptionWords) {
            String word = moduleDescriptionWord.replaceAll("[^a-zA-Z0-9_\\s-]", "");
            if (!word.equals("")) {
                moduleDescriptionList.add(word.toLowerCase());
            }
        }

        ArrayList<String> filteredModuleDescriptionList = new ArrayList<>();
        filteredModuleDescriptionList.addAll(moduleDescriptionList);
        for (String stopWord : stopWords) {
            filteredModuleDescriptionList.removeIf(word -> word.equalsIgnoreCase(stopWord));
        }

        moduleSearchKeywords = moduleSearchKeywords + " (";
        moduleDescriptionListField = filteredModuleDescriptionList;
        for (String moduleDescriptionWord : filteredModuleDescriptionList) {
            moduleSearchKeywords = moduleSearchKeywords + " " + moduleDescriptionWord + "*";
        }

        moduleSearchKeywords = moduleSearchKeywords + ")^" + mdBoostFactor;
        return moduleSearchKeywords;
    }

    private static String getProcessingFileSuffix(String language) {
        if (language == null) {
            return ".cttp";
        }
        String normalized = language.trim().toLowerCase();
        if (normalized.equals("py") || normalized.equals("python")) {
            return ".pytp";
        }
        if (normalized.equals("c") || normalized.equals("cc") || normalized.equals("cpp")
                || normalized.equals("cxx") || normalized.equals("c++")) {
            return ".cttp";
        }
        return ".jvtp";
    }
}

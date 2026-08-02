package ReflexionModel;

import cc.mallet.topics.ParallelTopicModel;
import cc.mallet.types.*;
import cc.mallet.pipe.*;
import cc.mallet.pipe.iterator.StringArrayIterator;

import java.io.*;
import java.util.*;
import java.nio.file.Paths;
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.logging.*;

public class ldaSimilarity {
    private ParallelTopicModel ldaModel;
    private Pipe ldaPipe;

    public ldaSimilarity(int numTopics) throws IOException {
        this.ldaModel = new ParallelTopicModel(numTopics);
        this.ldaPipe = buildPipe();
    }

    private Pipe buildPipe() throws IOException {
        // Disable Mallet's logging
        Logger malletLogger = Logger.getLogger("cc.mallet");
        malletLogger.setLevel(Level.OFF);
        for (Handler handler : malletLogger.getHandlers()) {
            handler.setLevel(Level.OFF);
        }
        List<Pipe> pipeList = new ArrayList<>();
        pipeList.add(new CharSequenceLowercase());
        pipeList.add(new CharSequence2TokenSequence());
        File stopwordsFile = createTempStopwordsFile();
        pipeList.add(new TokenSequenceRemoveStopwords(stopwordsFile, "UTF-8", false, false, false));
        pipeList.add(new TokenSequence2FeatureSequence());
        return new SerialPipes(pipeList);
    }

    public void trainLdaModel(String[] documents) {
        InstanceList instances = new InstanceList(ldaPipe);
        instances.addThruPipe(new StringArrayIterator(documents));
        ldaModel.addInstances(instances);
        ldaModel.setNumThreads(2);
        ldaModel.setNumIterations(1000);
        try {
            ldaModel.estimate();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public double[] getTopicDistribution(String document) {
        InstanceList testing = new InstanceList(ldaPipe);
        testing.addThruPipe(new Instance(document, null, "test instance", null));
        return ldaModel.getInferencer().getSampledDistribution(testing.get(0), 1000, 10, 10);
    }

    public double[] getEnhancedTopicDistribution(String moduleName, String moduleDescription, int boostFactor) {
        // Create an enhanced document by repeating the module name
        StringBuilder enhancedDocument = new StringBuilder();
        for (int i = 0; i < boostFactor; i++) {
            enhancedDocument.append(moduleName).append(" ");
        }
        enhancedDocument.append(moduleDescription);

        InstanceList testing = new InstanceList(ldaPipe);
        testing.addThruPipe(new Instance(enhancedDocument.toString(), null, "test instance", null));
        return ldaModel.getInferencer().getSampledDistribution(testing.get(0), 1000, 10, 10);
    }


    public Map<String, String> readCleanedFiles(String directoryPath, String processingFileSuffix, String project) {
        Path dirPath = Paths.get(directoryPath);
        Map<String, String> documentContents = new HashMap<>();

        try {
            List<Path> paths = Files.walk(dirPath)
                    .filter(Files::isRegularFile)
                    .filter(p -> p.toString().endsWith(processingFileSuffix))
                    .collect(Collectors.toList());

            for (Path path : paths) {
                StringBuilder contentBuilder = new StringBuilder();
                try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        contentBuilder.append(line).append(" ");
                    }
                } catch (IOException e) {
                    System.err.println("Error reading file: " + path);
                    e.printStackTrace();
                }
                documentContents.put(path.toString().substring(path.toString().indexOf(project)+project.length()+1), contentBuilder.toString().trim());
            }
        } catch (IOException e) {
            System.err.println("Error walking through directory: " + dirPath);
            e.printStackTrace();
        }

        return documentContents;
    }



    public double cosineSimilarity(double[] vec1, double[] vec2) {
        double dotProduct = 0.0;
        double normA = 0.0;
        double normB = 0.0;
        for (int i = 0; i < vec1.length; i++) {
            dotProduct += vec1[i] * vec2[i];
            normA += Math.pow(vec1[i], 2);
            normB += Math.pow(vec2[i], 2);
        }
        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }

    public static File createTempStopwordsFile() throws IOException {
        String[] stopwords = {
                "a", "able", "about", "above", "according", "accordingly", "across", "actually", "after", "afterwards", "again", "against",
                "all", "allow", "allows", "almost", "alone", "along", "already", "also", "although", "always", "am", "among", "amongst", "an",
                "and", "another", "any", "anybody", "anyhow", "anyone", "anything", "anyway", "anyways", "anywhere", "apart", "appear",
                "appreciate", "appropriate", "are", "around", "as", "aside", "ask", "asking", "associated", "at", "available", "away", "awfully",
                "b", "be", "became", "because", "become", "becomes", "becoming", "been", "before", "beforehand", "behind", "being", "believe",
                "below", "beside", "besides", "best", "better", "between", "beyond", "both", "brief", "but", "by", "c", "came", "can", "cannot",
                "cant", "cause", "causes", "certain", "certainly", "changes", "clearly", "co", "com", "come", "comes", "concerning", "consequently",
                "consider", "considering", "contain", "containing", "contains", "corresponding", "could", "course", "currently", "d", "definitely",
                "described", "despite", "did", "different", "do", "does", "doing", "done", "down", "downwards", "during", "e", "each", "edu", "eg",
                "eight", "either", "else", "elsewhere", "enough", "entirely", "especially", "et", "etc", "even", "ever", "every", "everybody",
                "everyone", "everything", "everywhere", "ex", "exactly", "example", "except", "f", "far", "few", "fifth", "first", "five", "followed",
                "following", "follows", "for", "former", "formerly", "forth", "four", "from", "further", "furthermore", "g", "get", "gets", "getting",
                "given", "gives", "go", "goes", "going", "gone", "got", "gotten", "greetings", "h", "had", "happens", "hardly", "has", "have", "having",
                "he", "hello", "help", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "hi", "him", "himself",
                "his", "hither", "hopefully", "how", "howbeit", "however", "i", "ie", "if", "ignored", "immediate", "in", "inasmuch", "inc", "indeed",
                "indicate", "indicated", "indicates", "inner", "insofar", "instead", "into", "inward", "is", "it", "its", "itself", "j", "just", "k",
                "keep", "keeps", "kept", "know", "knows", "known", "l", "last", "lately", "later", "latter", "latterly", "least", "less", "lest", "let",
                "like", "liked", "likely", "little", "look", "looking", "looks", "ltd", "m", "mainly", "many", "may", "maybe", "me", "mean", "meanwhile",
                "merely", "might", "more", "moreover", "most", "mostly", "much", "must", "my", "myself", "n", "name", "namely", "nd", "near", "nearly",
                "necessary", "need", "needs", "neither", "never", "nevertheless", "new", "next", "nine", "no", "nobody", "non", "none", "noone", "nor",
                "normally", "not", "nothing", "novel", "now", "nowhere", "o", "obviously", "of", "off", "often", "oh", "ok", "okay", "old", "on", "once",
                "one", "ones", "only", "onto", "or", "other", "others", "otherwise", "ought", "our", "ours", "ourselves", "out", "outside", "over",
                "overall", "own", "p", "particular", "particularly", "per", "perhaps", "placed", "please", "plus", "possible", "presumably", "probably",
                "provides", "q", "que", "quite", "qv", "r", "rather", "rd", "re", "really", "reasonably", "regarding", "regardless", "regards", "relatively",
                "respectively", "right", "s", "said", "same", "saw", "say", "saying", "says", "second", "secondly", "see", "seeing", "seem", "seemed",
                "seeming", "seems", "seen", "self", "selves", "sensible", "sent", "serious", "seriously", "seven", "several", "shall", "she", "should",
                "since", "six", "so", "some", "somebody", "somehow", "someone", "something", "sometime", "sometimes", "somewhat", "somewhere", "soon",
                "sorry", "specified", "specify", "specifying", "still", "sub", "such", "sup", "sure", "t", "take", "taken", "tell", "tends", "th", "than",
                "thank", "thanks", "thanx", "that", "thats", "the", "their", "theirs", "them", "themselves", "then", "thence", "there", "thereafter",
                "thereby", "therefore", "therein", "theres", "thereupon", "these", "they", "think", "third", "this", "thorough", "thoroughly", "those",
                "though", "three", "through", "throughout", "thru", "thus", "to", "together", "too", "took", "toward", "towards", "tried", "tries", "truly",
                "try", "trying", "twice", "two", "u", "un", "under", "unfortunately", "unless", "unlikely", "until", "unto", "up", "upon", "us", "use",
                "used", "useful", "uses", "using", "usually", "uucp", "v", "value", "various", "very", "via", "viz", "vs", "w", "want", "wants", "was",
                "way", "we", "welcome", "well", "went", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas",
                "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever", "whole", "whom", "whose", "why",
                "will", "willing", "wish", "with", "within", "without", "wonder", "would", "x", "y", "yes", "yet", "you", "your", "yours", "yourself",
                "yourselves", "z", "zero"
        };


        // Create a temporary file
        File tempFile = File.createTempFile("stopwords", ".txt");
        tempFile.deleteOnExit(); // Ensure the file is deleted when the JVM exits

        // Write the stopwords to the temporary file
        try (FileWriter writer = new FileWriter(tempFile)) {
            for (String word : stopwords) {
                writer.write(word + "\n");
            }
        }

        return tempFile;
    }


}

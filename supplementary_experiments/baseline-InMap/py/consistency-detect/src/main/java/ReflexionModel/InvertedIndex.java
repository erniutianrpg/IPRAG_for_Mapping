package ReflexionModel;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.*;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.store.RAMDirectory;
import org.apache.lucene.util.BytesRef;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class InvertedIndex {
    public static void run(String indexDir,String projectFolder,List<String> exclusionList) throws IOException, ParseException {

        Path newPath = Paths.get(indexDir);

        // If the folder exists, delete it first
        try {
            if(Files.exists(newPath)) {
                Files.walk(newPath)
                        .sorted(Comparator.reverseOrder())
                        .map(Path::toFile)
                        .forEach(File::delete);
            }

            // Create a new folder
            Files.createDirectory(newPath);
            System.out.println(indexDir+"Directory created successfully");
        } catch (IOException e) {
            e.printStackTrace();
        }

        // Open the folder to store the index
        FSDirectory dir = FSDirectory.open(Paths.get(indexDir));

        // Use the standard analyzer
        StandardAnalyzer analyzer = new StandardAnalyzer();

        // CreateIndexWriterconfiguration
        IndexWriterConfig config = new IndexWriterConfig(analyzer);

        // CreateIndexWriter
        IndexWriter writer = new IndexWriter(dir, config);

        // Open the folder of preprocessed documents
        File folder = new File(projectFolder);
        List<File> filePaths = traverseDirectory(folder);
        FieldType type = new FieldType();
        type.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS);
        type.setStored(true);
        type.setStoreTermVectors(true);
        type.setTokenized(true);
        type.setStoreTermVectorPositions(true);
        type.setStoreTermVectorOffsets(true);
        type.setStoreTermVectorPayloads(true);
        type.freeze();
        // Create a Lucenedocument and add it to the index
        for (File file : filePaths) {
            String filePath=file.toString();
            if ((file.isFile())&&(SourceFileProcessor.shouldIncludeFile(filePath))) {
//                            String content = new String(Files.readAllBytes(file.toPath()));

                // Preprocess file
                if (!Correctfilepath(filePath, exclusionList)) {
                    continue;
                }

                String cleanedTokens = SourceFileProcessor.preprocessFile(filePath);

                // Write the preprocessing result to a new file
                String outputFilePath = "E:\\Architecture\\InconsistencyDetect\\reflectionMaker\\test" + filePath.substring(filePath.lastIndexOf("\\"), filePath.lastIndexOf(".")) + ".txt";
                Files.writeString(Paths.get(outputFilePath), cleanedTokens);

                Document doc = new Document();
                doc.add(new StringField("path", file.toString(), Field.Store.YES));
                doc.add(new Field("contents", cleanedTokens, type));
                writer.addDocument(doc);
            }

                /*
                // Preprocess file
                if (!filePath.endsWith(".jvtp")){
                    continue;
                }
                Path file1 = Paths.get( filePath );
                InputStream stream = Files.newInputStream( file1 );
                String cleanedTokens = SourceFileProcessor.preprocessFile(filePath);

                // Write the preprocessing result to a new file
                String outputFilePath = "E:\\Architecture\\InconsistencyDetect\\reflectionMaker\\test"+filePath.substring(filePath.lastIndexOf("\\"),filePath.lastIndexOf("."))+".txt";
                Files.writeString(Paths.get(outputFilePath), cleanedTokens);

                Document doc = new Document();
                doc.add(new StringField("path", file.toString(), Field.Store.YES));
                doc.add(new TextField( "contents", new BufferedReader( new InputStreamReader( stream, StandardCharsets.UTF_8 ) ) ));
                writer.addDocument(doc);
            }
                 */
        }

        // Closewriterand commit changes

        writer.close();


//        // CreateDirectoryReaderandIndexSearcher
//        DirectoryReader reader = DirectoryReader.open(FSDirectory.open(Paths.get(indexDir)));
//        IndexSearcher searcher = new IndexSearcher(reader);
//        List<String>architectureModuleList=new ArrayList<>();
//        String dirPath = "E:\\Architecture\\InconsistencyDetect\\inmap-seed-mapping-main\\data\\architectures\\ant"; // Directory path to traverse
//        Path path = Paths.get(dirPath);
//        try (Stream<Path> paths = Files.walk(path)) {
//            architectureModuleList = paths
//                    .filter(Files::isDirectory)
//                    .map(Path::getFileName)
//                    .map(Path::toString)
//                    .collect(Collectors.toList());
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
////        architectureModuleList.add("BZip2Constants");
////        calculateSimilarities(architectureModuleList,searcher);
//
////        IndexReader reader1 = DirectoryReader.open(dir);
////        calculateTfIdfForTermsInDocument(reader,architectureModuleList);
////
////        calculateTfIdfForAllTermsInDocument(reader1);
//        // Create the search query; the searched field here is  "content",and the search term is the content in parser.parse("") 
//
//
//
//        QueryParser parser = new QueryParser("content", new StandardAnalyzer());
//        Query query = parser.parse("BZip2Constants");
//
//        // Execute search
//        TopDocs results = searcher.search(query, 10); // limit to the top 10results
//
//        System.out.println("Found  " + results.totalHits + " results.");
//
//        // Traverse and output results
//        for (ScoreDoc hit : results.scoreDocs) {
//            Document hitDoc = searcher.doc(hit.doc);
//            System.out.println("Matched document: " + hitDoc.get("filename") + ", score: " + hit.score); //contains not only tf-idf,also includes document length normalization and query boost (Query Boost)
//        }
//
//        // Close the reader
//        reader.close();


//

    }
    private static boolean Correctfilepath(String filePath, List<String> exclusionList) {
        if (!filePath.endsWith(".java")) {
            return false;
        }
        String[] parts = filePath.replaceAll(".java","").split("\\\\");  // split by backslash

        // Start from the index where 'src' or 'main' is located
        int startIndex = -1;
        for (int i = parts.length - 1; i >= 0; i--) {
            if (parts[i].equals("src") || parts[i].equals("main")) {
                startIndex = i + 1;
                break;
            }
        }
        if (startIndex == -1) {
            return false; // 'src' or 'main' not found
        }

        for (int endIndex = parts.length - 1; endIndex >= startIndex; endIndex--) {
            String[] subArray = Arrays.copyOfRange(parts, startIndex, endIndex + 1);
            String potentialModule = String.join(".", subArray);
            if (exclusionList.contains(potentialModule)){
                return false;
            }
        }

        // If no matching module found
        return true;
    }


    public static void calculateSimilarities(List<String> architectureModuleList, IndexSearcher searcher) {
        try {
            for (String module : architectureModuleList) {
                // Get the total number of documents
                int totalDocs = searcher.getIndexReader().numDocs();

                // Traverse all documents
                for (int i = 0; i < totalDocs; i++) {
                    Document doc = searcher.doc(i);
                    System.out.println("Processing document: " + doc.get("filename"));
                    Fields fields = searcher.getIndexReader().getTermVectors(i);
                    Terms termVector = searcher.getIndexReader().getTermVector(i, "content");
                    TermsEnum termsEnum = termVector.iterator();
                    PostingsEnum postingsEnum = null;

                    BytesRef term = null;
                    while ((term = termsEnum.next()) != null) {
                        String termText = term.utf8ToString();
                        if (termText.equals(module)) {
                            postingsEnum = termsEnum.postings(postingsEnum, PostingsEnum.NONE);
                            postingsEnum.nextDoc();
                            // computeTF
                            double tf = postingsEnum.freq();
                            // computeIDF
                            double idf = Math.log(totalDocs / (double) searcher.getIndexReader().docFreq(new Term("content", term)));
                            // computeTF-IDF
                            double tfIdf = tf * idf;
                            System.out.println("In document " + doc.get("filename") + ", module " + module + " has TF-IDF value: " + tfIdf);
                        }
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static Map<String, Double> calculateTfIdfForAllTermsInDocument(IndexReader indexReader) throws IOException {
        Map<String, Double> tfIdfForTerms = new HashMap<>();
        int num=indexReader.maxDoc();
        Terms vector = indexReader.getTermVector(indexReader.maxDoc() - 1, "content");
        TermsEnum termsEnum = vector.iterator();
        BytesRef term = null;
        while ((term = termsEnum.next()) != null) {
            String termText = term.utf8ToString();
            Term t = new Term("content", term);
            long df = indexReader.docFreq(t);
            long tf = termsEnum.totalTermFreq();
            double idf = Math.log((double) indexReader.numDocs() / (double) df);
            double tfIdf = tf * idf;
            tfIdfForTerms.put(termText, tfIdf);
        }
        return tfIdfForTerms;
    }

    public static Map<String, Double> calculateTfIdfForTermsInDocument(IndexReader indexReader, List<String> architectureModuleList) throws IOException {
        Map<String, Double> tfIdfForTerms = new HashMap<>();

        // Traverse all documents
        for (int docID = 0; docID < indexReader.maxDoc(); docID++) {
            Document doc = indexReader.document(docID);
            System.out.println("Processing document: " + doc.get("filename"));

//             Get the term vector of the current document
            Terms vector = indexReader.getTermVector(docID, "content");
            if (vector == null) {
                continue;
            }

            TermsEnum termsEnum = vector.iterator();

//             Traverse the query field list and compute each field's TF-IDFvalue
            for (String queryTerm : architectureModuleList) {

                Analyzer analyzer = new StandardAnalyzer();
                TokenStream tokenStream = analyzer.tokenStream("content", new StringReader(queryTerm));
                CharTermAttribute charTermAttribute = tokenStream.addAttribute(CharTermAttribute.class);
                // This is the part where processing starts
                tokenStream.reset();
                while (tokenStream.incrementToken()) {
                    String term = charTermAttribute.toString();

                    Term termInstance = new Term("content", term);
                    long termFreq = indexReader.totalTermFreq(termInstance);
                    System.out.println("The TF value of term " + term + " is: " + termFreq);

                    // Get the idfvalue
                    int docFreq = indexReader.docFreq(termInstance);
                    double idf1 = Math.log((double) indexReader.numDocs() / (double) docFreq);
                    System.out.println("The IDF value of term " + term + " is: " + idf1);
                    // Convert query fields to BytesRef
                    BytesRef term1 = new BytesRef(term);

                    // Logic for processing each term
                // If the current document term vector contains the query field, compute its TF-IDFvalue
                if (termsEnum.seekExact(term1)) {
                    long tf = termsEnum.totalTermFreq();
                    Term t = new Term("content", term1.utf8ToString());
                    long df = indexReader.docFreq(t);
                    double idf = Math.log((double) indexReader.numDocs() / (double) df);
                    double tfIdf = tf * idf;
                    tfIdfForTerms.put(queryTerm, tfIdf);
                    System.out.println("The TF-IDF value of term " + term + " is: " + tfIdf);
                }}
                tokenStream.end();
                tokenStream.close();
            }
        }

        return tfIdfForTerms;
    }

//    public static void calculateSimilarities(List<String> architectureModuleList, IndexSearcher indexSearcher) {
//        try {
//            int numDocs = indexSearcher.getIndexReader().numDocs();
//            for (String termString : architectureModuleList) {
//                Term term = new Term("contents", termString);
//
//                // Get term statistics
//                TermStatistics termStats;
//                termStats = indexSearcher.termStatistics(term, TermStates.build(indexSearcher.getIndexReader().getContext(), term,true));
//
//                Query query = new TermQuery(term);
//                TopDocs topDocs = indexSearcher.search(query, numDocs);
//
//                for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
//                    // Get the document's term frequency
//                    Terms terms = indexSearcher.getIndexReader().getTermVector(scoreDoc.doc, "contents");
//                    if (terms != null && terms.hasFreqs()) {
//                        TermsEnum termsEnum = terms.iterator();
//                        PostingsEnum postings = null;
//                        while (termsEnum.next() != null) {
//                            if (termsEnum.term().utf8ToString().equals(termString)) {
//                                postings = termsEnum.postings(postings, PostingsEnum.FREQS);
//                                postings.nextDoc();
//                                int tf = postings.freq();
//                                // computeidf
//                                double idf = Math.log(numDocs / (double) termStats.docFreq());
//                                // computetf-idf
//                                double tfIdf = tf * idf;
//                                System.out.println("Term: " + termString + ", DocID: " + scoreDoc.doc + ", TF-IDF: " + tfIdf);
//                            }
//                        }
//                    } else {
//                        System.err.println("Error getting term vector for doc: " + scoreDoc.doc);
//                    }
//                }
//            }
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }

    private static List<File> traverseDirectory(File directory) {
        List<File> filePaths = new ArrayList<>();

        if (directory == null || !directory.exists()) {
            System.out.println("Invalid directory path or directory does not exist.");
            return filePaths;
        }

        if (directory.isDirectory()) {
            File[] files = directory.listFiles();
            if (files != null) {
                for (File file : files) {
                    filePaths.addAll(traverseDirectory(file)); // Recursively call the method for subdirectories
                }
            }
        } else {
            // Add the file path to the list
            filePaths.add(directory);
        }

        return filePaths;
    }


}



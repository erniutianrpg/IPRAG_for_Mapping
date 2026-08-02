//package ReflexionModel;
//
//import ai.onnxruntime.*;
//
//import java.io.IOException;
//import java.nio.FloatBuffer;
//import java.util.*;
//
//
//public class BertSimilarity {
//    private static OrtEnvironment environment;
//    private static OrtSession session;
//
//    public BertSimilarity(String modelPath) throws OrtException {
//        environment = OrtEnvironment.getEnvironment();
//        session = environment.createSession(modelPath, new OrtSession.SessionOptions());
//    }
//
//    public static Map<String, Map<String, Double>> bertCalculate(String projectDir, String processingFileSuffix, String project, Map<String, String> moduleMap) throws IOException, OrtException {
//        BertSimilarity similarity = new BertSimilarity("path_to_your_model.onnx");
//        Map<String, String> documentContents = readCleanedFiles(projectDir, processingFileSuffix, project);
//
//        Map<String, Map<String, Double>> classToModuleScores = new HashMap<>();
//
//        for (Map.Entry<String, String> moduleEntry : moduleMap.entrySet()) {
//            String moduleName = moduleEntry.getKey();
//            String moduleDescription = moduleEntry.getValue();
//
//            double[] moduleVec = similarity.getVectorRepresentation(moduleDescription);
//
//            for (Map.Entry<String, String> entry : documentContents.entrySet()) {
//                String docPath = entry.getKey();
//                String docContent = entry.getValue();
//
//                double[] docVec = similarity.getVectorRepresentation(docContent);
//                double similarityScore = cosineSimilarity(moduleVec, docVec);
//
//                classToModuleScores.computeIfAbsent(docPath, k -> new HashMap<>()).put(moduleName, similarityScore);
//            }
//        }
//        return classToModuleScores;
//    }
//
//    // Process the input text to fit BERTthe model's preprocessing requirements
//
//    private float[] preprocessTextToFloatArray(String text) {
//        // Convert text to a sequence of token IDs
//        // Placeholder: actual implementation depends on the tokenizer logic
//        float[] ids = new float[128]; // Assuming a fixed size array for simplicity
//        Arrays.fill(ids, 0); // Initialize with zero (or padding token ID)
//        return ids;
//    }
//    // Load and preprocess the text, then get BERTvector representation
//    public double[] getVectorRepresentation(String text) throws OrtException {
//        // Preprocess the text and convert it to model input format
//        long[] shape = {1, 128}; // Assuming a fixed size input (e.g., BERT typically uses sequences of 128 tokens)
//        float[] inputData = preprocessTextToFloatArray(text); // Implement this method based on your tokenization logic
//
//        // Create a tensor from the preprocessed data
//        FloatBuffer floatBuffer = FloatBuffer.wrap(inputData);
//        OnnxTensor tensor = OnnxTensor.createTensor(environment, floatBuffer, shape);
//
//        // Prepare inputs for the session run
//        Map<String, OnnxTensor> inputs = Collections.singletonMap("input_ids", tensor);
//
//        // Execute the model
//        double[] vector;
//        try (OrtSession.Result result = session.run(inputs)) {
//            // Extract the output tensor and convert to double array
//            float[][] output = (float[][]) result.get(0).getValue();
//            vector = new double[output[0].length];
//            for (int i = 0; i < output[0].length; i++) {
//                vector[i] = output[0][i];
//            }
//        } finally {
//            tensor.close(); // Ensure the input tensor is closed
//        }
//
//        return vector;
//    }
//
//    private static double cosineSimilarity(double[] vec1, double[] vec2) {
//        double dotProduct = 0.0, normA = 0.0, normB = 0.0;
//        for (int i = 0; i < vec1.length; i++) {
//            dotProduct += vec1[i] * vec2[i];
//            normA += Math.pow(vec1[i], 2);
//            normB += Math.pow(vec2[i], 2);
//        }
//        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
//    }
//
//    private static Map<String, String> readCleanedFiles(String projectDir, String suffix, String project) {
//        // Implement file reading and text cleaning
//        return new HashMap<>();
//    }
//
//
//}

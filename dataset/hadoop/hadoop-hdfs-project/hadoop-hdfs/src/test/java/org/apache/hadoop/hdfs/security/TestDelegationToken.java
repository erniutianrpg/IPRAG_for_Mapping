/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.hadoop.hdfs.security;



import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.net.URI;
import java.security.PrivilegedExceptionAction;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.commons.logging.impl.Log4JLogger;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.hdfs.DFSConfigKeys;
import org.apache.hadoop.hdfs.DistributedFileSystem;
import org.apache.hadoop.hdfs.HdfsConfiguration;
import org.apache.hadoop.hdfs.MiniDFSCluster;
import org.apache.hadoop.hdfs.security.token.delegation.DelegationTokenIdentifier;
import org.apache.hadoop.hdfs.security.token.delegation.DelegationTokenSecretManager;
import org.apache.hadoop.hdfs.server.namenode.NameNodeAdapter;
import org.apache.hadoop.hdfs.server.namenode.web.resources.NamenodeWebHdfsMethods;
import org.apache.hadoop.hdfs.web.WebHdfsFileSystem;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.security.AccessControlException;
import org.apache.hadoop.security.UserGroupInformation;
import org.apache.hadoop.security.token.SecretManager.InvalidToken;
import org.apache.hadoop.security.token.Token;
import org.apache.log4j.Level;
import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

public class TestDelegationToken {
  private MiniDFSCluster cluster;
  private DelegationTokenSecretManager dtSecretManager;
  private Configuration config;
  private static final Log LOG = LogFactory.getLog(TestDelegationToken.class);
  
  @Before
  public void setUp() throws Exception {
    config = new HdfsConfiguration();
    config.setBoolean(DFSConfigKeys.DFS_WEBHDFS_ENABLED_KEY, true);
    config.setLong(DFSConfigKeys.DFS_NAMENODE_DELEGATION_TOKEN_MAX_LIFETIME_KEY, 10000);
    config.setLong(DFSConfigKeys.DFS_NAMENODE_DELEGATION_TOKEN_RENEW_INTERVAL_KEY, 5000);
    config.set("hadoop.security.auth_to_local",
        "RULE:[2:$1@$0](JobTracker@.*FOO.COM)s/@.*//" + "DEFAULT");
    FileSystem.setDefaultUri(config, "hdfs://localhost:" + "0");
    cluster = new MiniDFSCluster.Builder(config).numDataNodes(0).build();
    cluster.waitActive();
    dtSecretManager = NameNodeAdapter.getDtSecretManager(
        cluster.getNamesystem());
    dtSecretManager.startThreads();
  }

  @After
  public void tearDown() throws Exception {
    if(cluster!=null) {
      cluster.shutdown();
    }
  }

  private Token<DelegationTokenIdentifier> generateDelegationToken(
      String owner, String renewer) {
    DelegationTokenIdentifier dtId = new DelegationTokenIdentifier(new Text(
        owner), new Text(renewer), null);
    return new Token<DelegationTokenIdentifier>(dtId, dtSecretManager);
  }
  
  @Test
  public void testDelegationTokenSecretManager() throws Exception {
    Token<DelegationTokenIdentifier> token = generateDelegationToken(
        "SomeUser", "JobTracker");
    // Fake renewer should not be able to renew
    try {
  	  dtSecretManager.renewToken(token, "FakeRenewer");
  	  Assert.fail("should have failed");
    } catch (AccessControlException ace) {
      // PASS
    }
	  dtSecretManager.renewToken(token, "JobTracker");
    DelegationTokenIdentifier identifier = new DelegationTokenIdentifier();
    byte[] tokenId = token.getIdentifier();
    identifier.readFields(new DataInputStream(
             new ByteArrayInputStream(tokenId)));
    Assert.assertTrue(null != dtSecretManager.retrievePassword(identifier));
    LOG.info("Sleep to expire the token");
	  Thread.sleep(6000);
	  //Token should be expired
	  try {
	    dtSecretManager.retrievePassword(identifier);
	    //Should not come here
	    Assert.fail("Token should have expired");
	  } catch (InvalidToken e) {
	    //Success
	  }
	  dtSecretManager.renewToken(token, "JobTracker");
	  LOG.info("Sleep beyond the max lifetime");
	  Thread.sleep(5000);
	  try {
  	  dtSecretManager.renewToken(token, "JobTracker");
  	  Assert.fail("should have been expired");
	  } catch (InvalidToken it) {
	    // PASS
	  }
  }
  
  @Test 
  public void testCancelDelegationToken() throws Exception {
    Token<DelegationTokenIdentifier> token = generateDelegationToken(
        "SomeUser", "JobTracker");
    //Fake renewer should not be able to renew
    try {
      dtSecretManager.cancelToken(token, "FakeCanceller");
      Assert.fail("should have failed");
    } catch (AccessControlException ace) {
      // PASS
    }
    dtSecretManager.cancelToken(token, "JobTracker");
    try {
      dtSecretManager.renewToken(token, "JobTracker");
      Assert.fail("should have failed");
    } catch (InvalidToken it) {
      // PASS
    }
  }
  
  @Test
  public void testDelegationTokenDFSApi() throws Exception {
    DistributedFileSystem dfs = (DistributedFileSystem) cluster.getFileSystem();
    Token<DelegationTokenIdentifier> token = dfs.getDelegationToken("JobTracker");
    DelegationTokenIdentifier identifier = new DelegationTokenIdentifier();
    byte[] tokenId = token.getIdentifier();
    identifier.readFields(new DataInputStream(
             new ByteArrayInputStream(tokenId)));
    LOG.info("A valid token should have non-null password, and should be renewed successfully");
    Assert.assertTrue(null != dtSecretManager.retrievePassword(identifier));
    dtSecretManager.renewToken(token, "JobTracker");
  }
  
  @SuppressWarnings("deprecation")
  @Test
  public void testDelegationTokenWebHdfsApi() throws Exception {
    ((Log4JLogger)NamenodeWebHdfsMethods.LOG).getLogger().setLevel(Level.ALL);
    final String uri = WebHdfsFileSystem.SCHEME  + "://"
        + config.get(DFSConfigKeys.DFS_NAMENODE_HTTP_ADDRESS_KEY);
    //get file system as JobTracker
    final UserGroupInformation ugi = UserGroupInformation.createUserForTesting(
        "JobTracker", new String[]{"user"});
    final WebHdfsFileSystem webhdfs = ugi.doAs(
        new PrivilegedExceptionAction<WebHdfsFileSystem>() {
      @Override
      public WebHdfsFileSystem run() throws Exception {
        return (WebHdfsFileSystem)FileSystem.get(new URI(uri), config);
      }
    });

    final Token<DelegationTokenIdentifier> token = webhdfs.getDelegationToken("JobTracker");
    DelegationTokenIdentifier identifier = new DelegationTokenIdentifier();
    byte[] tokenId = token.getIdentifier();
    identifier.readFields(new DataInputStream(new ByteArrayInputStream(tokenId)));
    LOG.info("A valid token should have non-null password, and should be renewed successfully");
    Assert.assertTrue(null != dtSecretManager.retrievePassword(identifier));
    dtSecretManager.renewToken(token, "JobTracker");
  }

  @Test
  public void testDelegationTokenWithDoAs() throws Exception {
    final DistributedFileSystem dfs = (DistributedFileSystem) cluster.getFileSystem();
    final Token<DelegationTokenIdentifier> token = 
      dfs.getDelegationToken("JobTracker");
    final UserGroupInformation longUgi = UserGroupInformation
        .createRemoteUser("JobTracker/foo.com@FOO.COM");
    final UserGroupInformation shortUgi = UserGroupInformation
        .createRemoteUser("JobTracker");
    longUgi.doAs(new PrivilegedExceptionAction<Object>() {
      public Object run() throws IOException {
        final DistributedFileSystem dfs = (DistributedFileSystem) cluster
            .getFileSystem();
        try {
          //try renew with long name
          dfs.renewDelegationToken(token);
        } catch (IOException e) {
          Assert.fail("Could not renew delegation token for user "+longUgi);
        }
        return null;
      }
    });
    shortUgi.doAs(new PrivilegedExceptionAction<Object>() {
      public Object run() throws IOException {
        final DistributedFileSystem dfs = (DistributedFileSystem) cluster
            .getFileSystem();
        dfs.renewDelegationToken(token);
        return null;
      }
    });
    longUgi.doAs(new PrivilegedExceptionAction<Object>() {
      public Object run() throws IOException {
        final DistributedFileSystem dfs = (DistributedFileSystem) cluster
            .getFileSystem();
        try {
          //try cancel with long name
          dfs.cancelDelegationToken(token);
        } catch (IOException e) {
          Assert.fail("Could not cancel delegation token for user "+longUgi);
        }
        return null;
      }
    });
  }
 
}

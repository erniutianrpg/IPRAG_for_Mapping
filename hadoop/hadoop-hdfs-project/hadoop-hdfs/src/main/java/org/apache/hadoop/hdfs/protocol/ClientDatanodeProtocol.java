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
package org.apache.hadoop.hdfs.protocol;

import java.io.IOException;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.hadoop.classification.InterfaceAudience;
import org.apache.hadoop.classification.InterfaceStability;
import org.apache.hadoop.hdfs.DFSConfigKeys;
import org.apache.hadoop.hdfs.security.token.block.BlockTokenSelector;
import org.apache.hadoop.ipc.VersionedProtocol;
import org.apache.hadoop.security.KerberosInfo;
import org.apache.hadoop.security.token.TokenInfo;

/** An client-datanode protocol for block recovery
 */
@InterfaceAudience.Private
@InterfaceStability.Evolving
@KerberosInfo(
    serverPrincipal = DFSConfigKeys.DFS_DATANODE_USER_NAME_KEY)
@TokenInfo(BlockTokenSelector.class)
public interface ClientDatanodeProtocol extends VersionedProtocol {
  public static final Log LOG = LogFactory.getLog(ClientDatanodeProtocol.class);

  /**
   * 9: Added deleteBlockPool method
   */
  public static final long versionID = 9L;

  /** Return the visible length of a replica. */
  long getReplicaVisibleLength(ExtendedBlock b) throws IOException;
  
  /**
   * Refresh the list of federated namenodes from updated configuration
   * Adds new namenodes and stops the deleted namenodes.
   * 
   * @throws IOException on error
   **/
  void refreshNamenodes() throws IOException;

  /**
   * Delete the block pool directory. If force is false it is deleted only if
   * it is empty, otherwise it is deleted along with its contents.
   * 
   * @param bpid Blockpool id to be deleted.
   * @param force If false blockpool directory is deleted only if it is empty 
   *          i.e. if it doesn't contain any block files, otherwise it is 
   *          deleted along with its contents.
   * @throws IOException
   */
  void deleteBlockPool(String bpid, boolean force) throws IOException; 
}

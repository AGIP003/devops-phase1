 function Transaction  () {
 
 
    return (
        <div>
        {loading && <p>Loading...</p>}
                   {error && (
                       <p style={{ color: 'red' }}>
                           Error: {error} <button onClick={fetchTransactions}>Retry</button>
                       </p>
                   )}
               
                   {!error && (
                       <table border="1">
                           <thead>
                               <tr>
                                   <th>Date</th>
                                   <th>Description</th>
                                   <th>Type</th>
                                   <th>Category</th>
                                   <th>Amount</th>
                                   <th>Payment Method</th>
                                   <th>Actions</th>
                               </tr>
                           </thead>
                           <tbody>
                               {loading ? (
                                   [...Array(5)].map((_, i) => <TransactionSkelton key={i} />)

                               ) : filteredTransactions.length === 0 ? (
                                   <tr>
                                       <td colSpan={7} style={{ textAlign: 'center' }}>
                                           {transactions.length === 0
                                               ? 'No transactions yet.'
                                               : 'No transactions match your search/filter'}
                                       </td>
                                   </tr>

                               ) : (filteredTransactions.map((tx) => (
                                   <tr key={tx.id}>
                                       <td>{tx.date}</td>
                                       <td>{tx.description}</td>
                                       <td>{tx.type}</td>
                                       <td>{tx.category}</td>
                                       <td>{tx.amount}</td>
                                       <td>{tx.payment_method}</td>
                                       <td>
                                           <DeleteButton
                                               transactionId={tx.id}
                                               onDeleted={fetchTransactions}
                                           />
                                       </td>
                                   </tr>
                               ))
                               )}
                           </tbody>
                       </table>
                   )}
            </div>
            )       
       }
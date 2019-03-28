/* TAS */
/* -------------------------------------------------------- */
using System;
using System.Collections.Generic;
using CookComputing;
using CookComputing.XmlRpc;
using System.Data;
using System.Data.SqlClient;



/* Get Data Asset */
/* ======================================================================= */

namespace ConsoleXMLRPC
{
    [XmlRpcUrl("http://smart-leaders.dyndns.org:8068/xmlrpc/common")]
    public interface IOpenSIODLgn : IXmlRpcProxy
    {
        [XmlRpcMethod("login")]
        int login(string dbName, string dbUser, string dbPwd);
    }

    [XmlRpcUrl("http://smart-leaders.dyndns.org:8068/xmlrpc/object")]
    public interface IOpenSIODExec : IXmlRpcProxy
    {
        [XmlRpcMethod("execute")]
        Object Execute(string dbName, int userId, string pwd, string model, string method, int  asset);
    }

    class Program
    {
        static void Main(string[] args)
        {
            string dbname = "asset8";
            string username = "admin";
            string password = "admin";
            try
            {
                IOpenSIODLgn rpcOPenClient = (IOpenSIODLgn)XmlRpcProxyGen.Create(typeof(IOpenSIODLgn));
                int userid = rpcOPenClient.login(dbname, username, password);
                Console.WriteLine("Succes Login AADC, Uid : " + userid);

                int asset = 5;
                IOpenSIODExec rpcOPenClientExec = (IOpenSIODExec)XmlRpcProxyGen.Create(typeof(IOpenSIODExec));
                Object data = rpcOPenClientExec.Execute(dbname, userid, password, "data.asset", "getasset", asset);
                Console.WriteLine("ID ASSET " + data);
                Console.ReadLine();
            }
            catch (Exception ex)
            {
                Console.WriteLine("Error Login AADC" + ex.ToString());
            }
            Console.ReadLine();
        }
    }
}

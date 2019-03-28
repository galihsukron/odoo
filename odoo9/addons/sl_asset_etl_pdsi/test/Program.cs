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
    //[XmlRpcUrl("http://smart-leaders.dyndns.org:8068/xmlrpc/common")]
    [XmlRpcUrl("http://192.168.0.100:8078/xmlrpc/common")]
    public interface IOpenSIODLgn : IXmlRpcProxy
    {
        [XmlRpcMethod("login")]
        int login(string dbName, string dbUser, string dbPwd);
    }

    [XmlRpcUrl("http://192.168.0.100:8078/xmlrpc/object")]
    public interface IOpenSIODExec : IXmlRpcProxy
    {
        [XmlRpcMethod("execute")]
        Object[] Execute(string dbName, int userId, string pwd, string model, string method, string asset, string no_moveable, string tgl);
    }

    class Program
    {
        static void Main(string[] args)
        {
            string dbname = "asset14";
            string username = "admin";
            string password = "admin";
            try
            {
                IOpenSIODLgn rpcOPenClient = (IOpenSIODLgn)XmlRpcProxyGen.Create(typeof(IOpenSIODLgn));
                int userid = rpcOPenClient.login(dbname, username, password);
                Console.WriteLine("Succes Login AADC, Uid : " + userid);

                string asset = "";//"000000000000000000000052" // 3000E2003016740C0080172062D4, 3000E20032CDE5315A7131DD3569
                string no_moveable = ""; //"1" //"2" //"3"
                string tgl = "2016-07-27 12:36:35"; //"2016-07-19" //"2016-07-20"
                IOpenSIODExec rpcOPenClientExec = (IOpenSIODExec)XmlRpcProxyGen.Create(typeof(IOpenSIODExec));
                Object[] data = rpcOPenClientExec.Execute(dbname, userid, password, "data.asset", "getasset", asset, no_moveable, tgl);
                if (data[0].ToString() == "False")
                {
                    Console.WriteLine("Data Not Found");
                }
                else
                {
                    Console.WriteLine("Data Asset " + data);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("Error Login AADC" + ex.ToString());
            }
            Console.ReadLine();
        }
    }
}
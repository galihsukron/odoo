from odoo.tests import common
 
 
class TestComponentItem(common.TransactionCase):
    
    def test_component_item(self):
        
        component_1 = {}
        component_1['name']         = "Kayu"
        component_1["estimation"]   = 1
        comp1 = self.env["master.component"].create(component_1)
        
        component_2 = {}
        component_2['name']         = "Paku"
        component_2["estimation"]   = 1
        comp2 = self.env["master.component"].create(component_2)
        
        component_3 = {}
        component_3['name']         = "Lem"
        component_3["estimation"]   = 2
        comp3 = self.env["master.component"].create(component_3)
        
        
        item_1 = {}
        item_1["name"] = "Meja"
        item_1["start_date"] = "2019-07-30"
        item_1["component_ids"] = [(0,0,{"component_id" : comp1.id,"percentage":20.0}),
                                   (0,0,{"component_id" : comp2.id,"percentage":20.0})]
        item1 = self.env["master.item"].create(item_1)
        
        
        item_2 = {}
        item_2["name"] = "Kursi"
        item_2["start_date"] = "2019-07-30"
        item_2["component_ids"] = [(0,0,{"component_id" : comp1.id,"percentage":20.0}),
                                   (0,0,{"component_id" : comp2.id,"percentage":20.0}),
                                   (0,0,{"component_id" : comp3.id,"percentage":60.0})]
        item2 = self.env["master.item"].create(item_2)
        
        
        
        self.assertEqual(item1.name, 'Meja')
        self.assertEqual(item1.total_percentage, 40.0)
        self.assertEqual(str(item1.expected_date), "2019-08-01")
        
        
        self.assertEqual(item2.name, 'Kursi')
        self.assertEqual(item2.total_percentage, 100.0)
        self.assertEqual(str(item2.expected_date), "2019-08-03")
        
#         make the tests error1        
#         self.assertEqual(item2.total_percentage, 10.0)
#         self.assertEqual(str(item2.expected_date), "2019-08-05")
        
#         make test error2(error because percentage > 100)
#         item_3 = {}
#         item_3["name"] = "Lemari"
#         item_3["start_date"] = "2019-07-30"
#         item_3["component_ids"] = [(0,0,{"component_id" : comp1.id,"percentage":20.0}),
#                                    (0,0,{"component_id" : comp2.id,"percentage":30.0}),
#                                    (0,0,{"component_id" : comp3.id,"percentage":60.0})]
#         item3 = self.env["master.item"].create(item_3)
#         
                       
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Test Was Successfull")
        
        
        
        
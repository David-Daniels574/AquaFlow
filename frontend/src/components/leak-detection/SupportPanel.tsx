import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Phone, Mail, MessageCircle, BookOpen } from "lucide-react";
import { motion } from "framer-motion";

export function SupportPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Need Assistance?</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Our support team is here to help you resolve any issues.
        </p>
        
        <div className="space-y-3">
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="flex items-center space-x-3 text-sm"
          >
            <Phone className="h-4 w-4 text-primary" />
            <span>+91 80 1234 5678</span>
          </motion.div>
          
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="flex items-center space-x-3 text-sm"
          >
            <Mail className="h-4 w-4 text-primary" />
            <span>support@aquaflow.in</span>
          </motion.div>
          
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="flex items-center space-x-3 text-sm"
          >
            <MessageCircle className="h-4 w-4 text-primary" />
            <span>Live Chat (24/7)</span>
          </motion.div>
        </div>
        
        <motion.div 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Button className="w-full bg-primary hover:bg-primary-hover">
            Contact Support
          </Button>
        </motion.div>
        
        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="flex items-center justify-center space-x-2 pt-2"
        >
          <BookOpen className="h-4 w-4 text-muted-foreground" />
          <Button variant="link" className="p-0 h-auto text-sm">
            Visit Knowledge Base
          </Button>
        </motion.div>
      </CardContent>
    </Card>
  );
}
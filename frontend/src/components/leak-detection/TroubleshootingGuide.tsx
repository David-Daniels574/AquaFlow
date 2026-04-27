import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { motion } from "framer-motion";

const troubleshootingSteps = [
  {
    id: "visible-pipes",
    title: "Check Visible Pipes and Fixtures",
    content: "Inspect all exposed pipes under sinks, near water heaters, and in basements for drips or wet spots. Check toilet bases and showerheads for leaks. Listen for running water when no appliances are in use."
  },
  {
    id: "water-meter",
    title: "Monitor Your Water Meter",
    content: "Turn off all water sources and check if the meter is still running. If it continues to move, you likely have a leak. Note the meter reading and check again after 1-2 hours to measure usage."
  },
  {
    id: "irrigation-systems",
    title: "Inspect Irrigation Systems",
    content: "Check sprinkler heads for damage or continuous dripping. Inspect drip irrigation lines for clogs or breaks. Look for unusually green or soggy areas in your lawn that might indicate underground leaks."
  },
  {
    id: "professional-help",
    title: "Consider Professional Help",
    content: "If you can't locate the source, contact a plumber for leak detection services. Professional equipment can find hidden leaks behind walls or underground. Document any findings for insurance purposes."
  }
];

export function TroubleshootingGuide() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Troubleshooting Guide</CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          {troubleshootingSteps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <AccordionItem value={step.id}>
                <AccordionTrigger className="text-left">
                  {step.title}
                </AccordionTrigger>
                <AccordionContent className="text-sm text-muted-foreground leading-relaxed">
                  {step.content}
                </AccordionContent>
              </AccordionItem>
            </motion.div>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}